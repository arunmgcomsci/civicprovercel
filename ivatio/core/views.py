"""
CivicPro Views
Complete view logic including Haversine distance calculations,
authentication, worker/employer dashboards, and hiring workflow.
"""

import math
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg, Count
from django.utils import timezone

from .models import (
    UserProfile, HireRequest, Review, WorkerAvailabilityLog,
    EmergencyCall, geocode_location, SupportConversation, SupportMessage
)
from .ai_support import get_ai_support_response, get_user_context
from .forms import (
    WorkerRegistrationForm, EmployerRegistrationForm,
    WorkerProfileForm, HireRequestForm, ReviewForm, WorkerSearchForm
)


# ─────────────────────────────────────────────
#  HAVERSINE DISTANCE CALCULATION
# ─────────────────────────────────────────────

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine Formula. Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def get_workers_with_distance(user_lat, user_lng, skill=None, radius=50):
    """
    Fetch available workers with distance from user's location.
    Returns sorted list (closest first) within the given radius.
    """
    queryset = UserProfile.objects.filter(
        role='WORKER',
        is_available=True,
        latitude__isnull=False,
        longitude__isnull=False,
    ).select_related('user')

    if skill:
        queryset = queryset.filter(skill_category=skill)

    workers_with_distance = []
    for worker in queryset:
        dist = haversine_distance(user_lat, user_lng, worker.latitude, worker.longitude)
        if dist <= radius:
            workers_with_distance.append({
                'worker': worker,
                'distance': round(dist, 1),
            })

    workers_with_distance.sort(key=lambda x: x['distance'])
    return workers_with_distance


# ─────────────────────────────────────────────
#  HOME / LANDING PAGE
# ─────────────────────────────────────────────

def home(request):
    """Landing page with platform stats"""
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.role == 'WORKER':
                return redirect('worker_dashboard')
            elif profile.role == 'EMPLOYER':
                return redirect('employer_dashboard')
        except UserProfile.DoesNotExist:
            pass

    # Stats for landing page
    total_workers = UserProfile.objects.filter(role='WORKER').count()
    available_workers = UserProfile.objects.filter(role='WORKER', is_available=True).count()
    total_hires = HireRequest.objects.filter(status='COMPLETED').count()
    total_employers = UserProfile.objects.filter(role='EMPLOYER').count()

    context = {
        'total_workers': total_workers,
        'available_workers': available_workers,
        'total_hires': total_hires,
        'total_employers': total_employers,
        'skill_choices': UserProfile.SKILL_CHOICES,
    }
    return render(request, 'home.html', context)


# ─────────────────────────────────────────────
#  AUTHENTICATION VIEWS
# ─────────────────────────────────────────────

def register_worker(request):
    """Worker registration with profile setup"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            # Create UserProfile for worker
            UserProfile.objects.create(
                user=user,
                role='WORKER',
                phone=form.cleaned_data['phone'],
                skill_category=form.cleaned_data['skill_category'],
                daily_rate=form.cleaned_data['daily_rate'],
                experience_years=form.cleaned_data['experience_years'],
                location_name=form.cleaned_data['location_name'],
            )

            login(request, user)
            messages.success(request, f"Welcome to CivicPro, {user.first_name}! Complete your profile to start getting hired.")
            return redirect('worker_profile_setup')
    else:
        form = WorkerRegistrationForm()

    return render(request, 'register_worker.html', {'form': form})


def register_employer(request):
    """Employer registration"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = EmployerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            UserProfile.objects.create(
                user=user,
                role='EMPLOYER',
                phone=form.cleaned_data.get('phone', ''),
            )

            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! You can now search and hire skilled workers.")
            return redirect('employer_dashboard')
    else:
        form = EmployerRegistrationForm()

    return render(request, 'register_employer.html', {'form': form})


def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.POST.get('next') or request.GET.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'login.html')


def logout_view(request):
    """Logout"""
    logout(request)
    messages.info(request, "You have been logged out. See you soon!")
    return redirect('login')


# ─────────────────────────────────────────────
#  WORKER VIEWS
# ─────────────────────────────────────────────

@login_required
def worker_profile_setup(request):
    """Worker profile creation / editing"""
    try:
        profile = request.user.profile
        if profile.role != 'WORKER':
            messages.error(request, "This page is for workers only.")
            return redirect('home')
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user, role='WORKER')

    if request.method == 'POST':
        form = WorkerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profile updated successfully!")
            return redirect('worker_dashboard')
    else:
        form = WorkerProfileForm(instance=profile)

    return render(request, 'worker_profile_setup.html', {'form': form, 'profile': profile})


@login_required
def worker_dashboard(request):
    """Worker dashboard — stats, hire requests, and availability toggle"""
    try:
        profile = request.user.profile
        if profile.role != 'WORKER':
            return redirect('employer_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('worker_profile_setup')

    hire_requests = HireRequest.objects.filter(
        worker=profile
    ).select_related('employer').order_by('-created_at')

    # Stats
    pending_count = hire_requests.filter(status='PENDING').count()
    active_count = hire_requests.filter(status='ACCEPTED').count()
    completed_count = hire_requests.filter(status='COMPLETED').count()
    reviews = profile.reviews_received.all().order_by('-created_at')

    context = {
        'profile': profile,
        'hire_requests': hire_requests,
        'pending_count': pending_count,
        'active_count': active_count,
        'completed_count': completed_count,
        'reviews': reviews,
        'avg_rating': profile.avg_rating(),
    }
    return render(request, 'worker_dashboard.html', context)


@login_required
@require_POST
def toggle_availability(request):
    """AJAX endpoint to toggle worker availability"""
    try:
        profile = request.user.profile
        if profile.role != 'WORKER':
            return JsonResponse({'error': 'Not a worker'}, status=403)

        profile.is_available = not profile.is_available
        profile.save()

        # Log the change
        WorkerAvailabilityLog.objects.create(
            worker=profile,
            became_available=profile.is_available
        )

        return JsonResponse({
            'status': 'ok',
            'is_available': profile.is_available,
            'message': '✅ You are now Available for Work!' if profile.is_available else '🔴 Status set to Busy'
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)


@login_required
@require_POST
def respond_hire_request(request, pk):
    """Worker accepts or rejects a hire request"""
    hire_req = get_object_or_404(HireRequest, pk=pk, worker=request.user.profile)
    action = request.POST.get('action')

    if action == 'accept' and hire_req.status == 'PENDING':
        hire_req.status = 'ACCEPTED'
        hire_req.save()
        messages.success(request, f"✅ You accepted the job request from {hire_req.employer.get_full_name() or hire_req.employer.username}!")
    elif action == 'reject' and hire_req.status == 'PENDING':
        hire_req.status = 'REJECTED'
        hire_req.save()
        messages.info(request, "Request rejected.")
    elif action == 'complete' and hire_req.status == 'ACCEPTED':
        hire_req.status = 'COMPLETED'
        hire_req.save()
        messages.success(request, "🎉 Job marked as Completed! The employer can now leave a review.")

    return redirect('worker_dashboard')


# ─────────────────────────────────────────────
#  EMPLOYER VIEWS
# ─────────────────────────────────────────────

@login_required
def employer_dashboard(request):
    """Employer dashboard — sent requests, stats"""
    try:
        profile = request.user.profile
        if profile.role != 'EMPLOYER':
            return redirect('worker_dashboard')
    except UserProfile.DoesNotExist:
        profile = None

    hire_requests = HireRequest.objects.filter(
        employer=request.user
    ).select_related('worker', 'worker__user').order_by('-created_at')

    pending = hire_requests.filter(status='PENDING').count()
    active = hire_requests.filter(status='ACCEPTED').count()
    completed = hire_requests.filter(status='COMPLETED').count()

    # Requests eligible for review
    completable = hire_requests.filter(status='COMPLETED')
    reviewable_ids = []
    for h in completable:
        if h.can_review():
            reviewable_ids.append(h.id)

    context = {
        'profile': profile,
        'hire_requests': hire_requests,
        'pending': pending,
        'active': active,
        'completed': completed,
        'reviewable_ids': reviewable_ids,
        'review_form': ReviewForm(),
    }
    return render(request, 'employer_dashboard.html', context)


@login_required
def search_workers(request):
    """
    Main worker search page with Haversine-based proximity sorting.
    Displays interactive Leaflet.js map with worker pins.
    """
    profile = None
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = None

    form = WorkerSearchForm(request.GET)

    location_query = request.GET.get('location', '').strip()

    # Determine default location based on user profile if available, else Bangalore
    default_lat = 12.9716
    default_lng = 77.5946
    if profile and profile.latitude and profile.longitude:
        default_lat = profile.latitude
        default_lng = profile.longitude

    try:
        user_lat = float(request.GET.get('lat', default_lat))
        user_lng = float(request.GET.get('lng', default_lng))
    except (ValueError, TypeError):
        user_lat = default_lat
        user_lng = default_lng

    # If location text query was provided, geocode it
    if location_query:
        g_lat, g_lng = geocode_location(location_query)
        if g_lat is not None and g_lng is not None:
            user_lat = g_lat
            user_lng = g_lng

    # Text display for the location search input
    if location_query:
        location_display = location_query
    elif profile and profile.location_name:
        location_display = profile.location_name
    else:
        location_display = f"{user_lat:.4f}, {user_lng:.4f}"

    try:
        radius = int(request.GET.get('radius', 10))
    except (ValueError, TypeError):
        radius = 10

    skill = request.GET.get('skill', '')

    workers_data = get_workers_with_distance(user_lat, user_lng, skill or None, radius)

    # Prepare JSON data for Leaflet map
    map_workers = []
    for item in workers_data:
        w = item['worker']
        map_workers.append({
            'id': w.id,
            'name': w.user.get_full_name() or w.user.username,
            'skill': w.get_skill_category_display(),
            'skill_icon': w.get_skill_display_icon(),
            'rate': float(w.daily_rate) if w.daily_rate else 0,
            'experience': w.experience_years,
            'location': w.location_name,
            'distance': item['distance'],
            'rating': w.avg_rating(),
            'lat': float(w.latitude) if w.latitude is not None else None,
            'lng': float(w.longitude) if w.longitude is not None else None,
            'is_verified': w.is_verified,
            'url': f"/worker/{w.id}/",
        })

    context = {
        'form': form,
        'workers_data': workers_data,
        'map_workers_json': json.dumps(map_workers),
        'user_lat': user_lat,
        'user_lng': user_lng,
        'radius': radius,
        'skill': skill,
        'location_display': location_display,
        'skill_choices': UserProfile.SKILL_CHOICES,
        'radius_options': [2, 5, 10, 25, 50, 100],
        'total_found': len(workers_data),
    }
    return render(request, 'employer_search_directory.html', context)


@login_required
def worker_detail(request, pk):
    """Full worker profile detail page"""
    worker = get_object_or_404(UserProfile, pk=pk, role='WORKER')
    reviews = worker.reviews_received.select_related('employer').order_by('-created_at')
    hire_form = HireRequestForm()

    # Calculate distance if employer has set location
    distance = None
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    if user_lat and user_lng and worker.latitude and worker.longitude:
        try:
            distance = round(haversine_distance(
                float(user_lat), float(user_lng),
                worker.latitude, worker.longitude
            ), 1)
        except (ValueError, TypeError):
            pass

    # Check if current employer already has a pending/active request
    existing_request = None
    if request.user.is_authenticated:
        existing_request = HireRequest.objects.filter(
            employer=request.user,
            worker=worker,
            status__in=['PENDING', 'ACCEPTED']
        ).first()

    context = {
        'worker': worker,
        'reviews': reviews,
        'hire_form': hire_form,
        'distance': distance,
        'existing_request': existing_request,
        'avg_rating': worker.avg_rating(),
        'total_jobs': worker.total_jobs(),
        'star_range': range(1, 6),
    }
    return render(request, 'worker_detail.html', context)


@login_required
@require_POST
def send_hire_request(request, worker_pk):
    """Send a direct hire request to a worker"""
    worker = get_object_or_404(UserProfile, pk=worker_pk, role='WORKER')

    try:
        profile = request.user.profile
        if profile.role != 'EMPLOYER':
            messages.error(request, "Only employers can send hire requests.")
            return redirect('worker_detail', pk=worker_pk)
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile first.")
        return redirect('worker_detail', pk=worker_pk)

    # Prevent duplicate active requests
    if HireRequest.objects.filter(
        employer=request.user, worker=worker, status__in=['PENDING', 'ACCEPTED']
    ).exists():
        messages.warning(request, "You already have an active request with this worker.")
        return redirect('worker_detail', pk=worker_pk)

    form = HireRequestForm(request.POST)
    if form.is_valid():
        hire_req = form.save(commit=False)
        hire_req.employer = request.user
        hire_req.worker = worker
        hire_req.save()
        messages.success(request, f"🎯 Hire request sent to {worker.user.get_full_name() or worker.user.username}! They will review and respond shortly.")
    else:
        messages.error(request, "Please fill in all required fields.")

    return redirect('worker_detail', pk=worker_pk)


@login_required
@require_POST
def submit_review(request, hire_request_pk):
    """Submit a review after job completion"""
    hire_req = get_object_or_404(HireRequest, pk=hire_request_pk, employer=request.user, status='COMPLETED')

    if not hire_req.can_review():
        messages.warning(request, "Review already submitted for this job.")
        return redirect('employer_dashboard')

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.worker = hire_req.worker
        review.employer = request.user
        review.hire_request = hire_req
        review.save()
        messages.success(request, "⭐ Thank you! Your review has been submitted.")
    else:
        messages.error(request, "Invalid review data. Please try again.")

    return redirect('employer_dashboard')


@login_required
def mark_hire_completed(request, pk):
    """Employer marks a hire request as completed"""
    hire_req = get_object_or_404(HireRequest, pk=pk, employer=request.user, status='ACCEPTED')
    hire_req.status = 'COMPLETED'
    hire_req.save()
    messages.success(request, "✅ Job marked as Completed! You can now leave a review.")
    return redirect('employer_dashboard')


# ─────────────────────────────────────────────
#  API ENDPOINTS (for AJAX)
# ─────────────────────────────────────────────

@login_required
def api_workers_nearby(request):
    """
    JSON API: Returns nearby workers for Leaflet map.
    Query params: lat, lng, radius, skill
    """
    try:
        lat = float(request.GET.get('lat', 12.9716))
        lng = float(request.GET.get('lng', 77.5946))
        radius = float(request.GET.get('radius', 10))
        skill = request.GET.get('skill', '')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    workers_data = get_workers_with_distance(lat, lng, skill or None, radius)

    result = []
    for item in workers_data:
        w = item['worker']
        result.append({
            'id': w.id,
            'name': w.user.get_full_name() or w.user.username,
            'skill': w.get_skill_category_display(),
            'skill_icon': w.get_skill_display_icon(),
            'rate': float(w.daily_rate) if w.daily_rate else 0,
            'experience': w.experience_years,
            'location': w.location_name,
            'distance': item['distance'],
            'rating': w.avg_rating(),
            'lat': w.latitude,
            'lng': w.longitude,
            'is_verified': w.is_verified,
            'url': f"/worker/{w.id}/",
        })

    return JsonResponse({'workers': result, 'count': len(result)})


def api_geocode(request):
    """
    JSON API: Geocode a query string (city or locality) to latitude and longitude.
    Query param: q
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'status': 'error', 'message': 'No search query provided'}, status=400)

    lat, lng = geocode_location(query)
    if lat is not None and lng is not None:
        return JsonResponse({'status': 'ok', 'lat': lat, 'lng': lng, 'query': query})
    return JsonResponse({'status': 'not_found', 'message': f'Could not find coordinates for "{query}"'}, status=404)


@login_required
@require_POST
def trigger_emergency(request):
    service_type = request.POST.get('service_type', 'GENERAL')
    condition = request.POST.get('condition', 'Panic / Urgent')

    # End any previous active calls first to avoid duplication
    EmergencyCall.objects.filter(user=request.user, status='ACTIVE').update(
        status='ENDED', ended_at=timezone.now()
    )

    # Try getting coordinates from profile
    latitude = None
    longitude = None
    location_name = ""
    try:
        profile = request.user.profile
        latitude = profile.latitude
        longitude = profile.longitude
        location_name = profile.location_name
    except UserProfile.DoesNotExist:
        pass

    call = EmergencyCall.objects.create(
        user=request.user,
        service_type=service_type,
        status='ACTIVE',
        condition=condition,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name
    )
    return JsonResponse({'status': 'ok', 'call_id': call.id})


@login_required
@require_POST
def end_emergency(request):
    EmergencyCall.objects.filter(user=request.user, status='ACTIVE').update(
        status='ENDED', ended_at=timezone.now()
    )
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def update_emergency_status(request):
    condition = request.POST.get('condition', 'Panic / Urgent')
    EmergencyCall.objects.filter(user=request.user, status='ACTIVE').update(
        condition=condition
    )
    return JsonResponse({'status': 'ok'})


@login_required
def get_active_emergency(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return JsonResponse({'active': False})

    # 1. Check if current user has their own active emergency
    own_call = EmergencyCall.objects.filter(user=request.user, status='ACTIVE').first()
    if own_call:
        return JsonResponse({
            'active': True,
            'is_own': True,
            'service_type': own_call.service_type,
            'condition': own_call.condition,
            'created_at': own_call.created_at.isoformat(),
            'elapsed_seconds': int((timezone.now() - own_call.created_at).total_seconds()),
            'user_details': {
                'name': request.user.get_full_name() or request.user.username,
                'phone': profile.phone,
                'location': profile.location_name,
                'medical_conditions': profile.medical_conditions if profile.role == 'WORKER' else '',
            }
        })

    # 2. Check if user is an Employer and their hired worker has an active emergency
    if profile.role == 'EMPLOYER':
        # Find active accepted hire requests for this employer
        active_hires = HireRequest.objects.filter(employer=request.user, status='ACCEPTED')
        for hire in active_hires:
            worker_user = hire.worker.user
            worker_call = EmergencyCall.objects.filter(user=worker_user, status='ACTIVE').first()
            if worker_call:
                return JsonResponse({
                    'active': True,
                    'is_own': False,
                    'service_type': worker_call.service_type,
                    'condition': worker_call.condition,
                    'created_at': worker_call.created_at.isoformat(),
                    'elapsed_seconds': int((timezone.now() - worker_call.created_at).total_seconds()),
                    'user_details': {
                        'name': worker_user.get_full_name() or worker_user.username,
                        'id': hire.worker.id,
                        'phone': hire.worker.phone,
                        'location': hire.worker.location_name or hire.work_location or "Unknown",
                        'medical_conditions': hire.worker.medical_conditions,
                        'role': 'WORKER'
                    }
                })

    # 3. Check if user is a Worker and their active employer has an active emergency
    if profile.role == 'WORKER':
        active_hires = HireRequest.objects.filter(worker=profile, status='ACCEPTED')
        for hire in active_hires:
            employer_user = hire.employer
            employer_call = EmergencyCall.objects.filter(user=employer_user, status='ACTIVE').first()
            if employer_call:
                try:
                    emp_profile = employer_user.profile
                    emp_phone = emp_profile.phone
                except UserProfile.DoesNotExist:
                    emp_phone = ""
                return JsonResponse({
                    'active': True,
                    'is_own': False,
                    'service_type': employer_call.service_type,
                    'condition': employer_call.condition,
                    'created_at': employer_call.created_at.isoformat(),
                    'elapsed_seconds': int((timezone.now() - employer_call.created_at).total_seconds()),
                    'user_details': {
                        'name': employer_user.get_full_name() or employer_user.username,
                        'phone': emp_phone,
                        'location': hire.work_location or "Hired Site",
                        'medical_conditions': '',
                        'role': 'EMPLOYER'
                    }
                })

    return JsonResponse({'active': False})


@login_required
def emergency_view(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile details first.")
        return redirect('home')

    context = {
        'profile': profile,
        'role': profile.role,
    }
    return render(request, 'emergency.html', context)


# ─────────────────────────────────────────────
#  CUSTOMER SUPPORT & AI EXECUTIVE
# ─────────────────────────────────────────────

def _get_or_create_support_conversation(request, conversation_id=None):
    """
    Helper to fetch or initialize an active support conversation
    for either an authenticated user or a session-tracked visitor.
    """
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    conv = None
    if conversation_id:
        conv = SupportConversation.objects.filter(id=conversation_id).first()

    if not conv:
        if request.user.is_authenticated:
            conv = SupportConversation.objects.filter(user=request.user, status='OPEN').order_by('-updated_at').first()
        else:
            conv = SupportConversation.objects.filter(session_key=session_key, status='OPEN').order_by('-updated_at').first()

    if not conv:
        conv = SupportConversation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key or "",
            status='OPEN',
            subject='General Inquiry'
        )
    return conv


def support_hub(request):
    """
    Dedicated Customer Support Center page with FAQs,
    quick contact info, and integrated AI executive chat interface.
    """
    faqs = [
        {
            'q': 'How do I find and hire a worker near me?',
            'a': 'Simply log in to your account and click "Find Workers" in the navigation bar. You can choose a trade (like Electrician or Plumber), enter your location or use device GPS, and adjust the radius slider up to 50 km. Click any worker card to view their profile, daily rate, verified status, and click "Send Hire Request".'
        },
        {
            'q': 'How do payments and daily wages work?',
            'a': 'CivicPro operates on a 100% transparent, zero-commission model. Workers set their own daily wage rates directly. Employers pay workers directly in cash or UPI at the end of the work day. CivicPro does not deduct any fees or platform cuts.'
        },
        {
            'q': 'How do I register as a skilled daily-wage worker?',
            'a': 'Click "Join as Worker" on the homepage or register page. Once registered, complete your profile setup by selecting your trade, daily wage rate (₹), years of experience, and location. You can toggle your status to "Available" so employers can discover and hire you.'
        },
        {
            'q': 'What is the Verified Worker badge?',
            'a': 'A Verified Badge indicates that the worker\'s identity, trade experience, and contact details have been reviewed by our administrative team. It boosts your trust score and helps you get more hiring requests.'
        },
        {
            'q': 'How does the Emergency SOS service work on worksites?',
            'a': 'Our Emergency Services system provides rapid one-click dispatch for Medical / Ambulance (108), Police (112), and Fire Force (101). When an emergency is triggered, it instantly alerts the connected worker or employer on site with location details and medical notes.'
        },
        {
            'q': 'How can I contact a human administrator?',
            'a': 'You can escalate any chat with our AI Support Executive Maya by typing "Speak with human admin" or emailing support@civicpro.in. Escalated tickets are tracked directly in the platform management portal.'
        }
    ]

    conv = _get_or_create_support_conversation(request)
    messages_list = conv.messages.all().order_by('created_at')
    user_ctx = get_user_context(request.user if request.user.is_authenticated else None)

    context = {
        'faqs': faqs,
        'conversation': conv,
        'initial_messages': messages_list,
        'user_ctx': user_ctx,
    }
    return render(request, 'support.html', context)


def api_support_chat(request):
    """
    JSON API for sending a message to the AI Support Executive
    and receiving an intelligent, formatted reply with quick chips.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')

    if not message:
        return JsonResponse({'status': 'error', 'message': 'Message cannot be empty.'}, status=400)

    conv = _get_or_create_support_conversation(request, conversation_id)

    # Save user message
    SupportMessage.objects.create(
        conversation=conv,
        sender='USER',
        message=message
    )

    # Fetch recent message history
    recent_msgs = conv.messages.all().order_by('-created_at')[:8]
    history = [{'sender': m.sender, 'text': m.message} for m in reversed(list(recent_msgs))]

    # Generate response
    ai_result = get_ai_support_response(message, user=request.user if request.user.is_authenticated else None, history=history)

    # Save AI response
    SupportMessage.objects.create(
        conversation=conv,
        sender='AI',
        message=ai_result['reply']
    )

    # Update conversation status if escalated
    if ai_result.get('escalated'):
        conv.status = 'ESCALATED'

    if conv.subject == 'General Inquiry' and ai_result.get('subject'):
        conv.subject = ai_result['subject']

    conv.save()

    return JsonResponse({
        'status': 'success',
        'conversation_id': conv.id,
        'reply': ai_result['reply'],
        'chips': ai_result.get('chips', []),
        'escalated': conv.status == 'ESCALATED',
        'timestamp': timezone.now().strftime('%I:%M %p')
    })


def api_support_history(request):
    """
    Fetches the chat transcript for the active support conversation.
    """
    conv = _get_or_create_support_conversation(request)
    messages_data = [
        {
            'id': m.id,
            'sender': m.sender,
            'message': m.message,
            'created_at': m.created_at.strftime('%I:%M %p')
        }
        for m in conv.messages.all().order_by('created_at')
    ]

    return JsonResponse({
        'status': 'success',
        'conversation_id': conv.id,
        'conversation_status': conv.status,
        'messages': messages_data,
    })


def api_support_clear(request):
    """
    Clears the current chat session by resolving previous conversation
    and creating a fresh one.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required.'}, status=405)

    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    if request.user.is_authenticated:
        SupportConversation.objects.filter(user=request.user, status='OPEN').update(status='RESOLVED')
    else:
        SupportConversation.objects.filter(session_key=session_key, status='OPEN').update(status='RESOLVED')

    new_conv = SupportConversation.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key or "",
        status='OPEN',
        subject='New Inquiry'
    )

    return JsonResponse({
        'status': 'success',
        'conversation_id': new_conv.id,
        'message': 'Chat session reset.'
    })


def api_support_escalate(request):
    """
    Explicitly marks conversation as ESCALATED to human administrators.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required.'}, status=405)

    conv = _get_or_create_support_conversation(request)
    conv.status = 'ESCALATED'
    conv.save()

    SupportMessage.objects.create(
        conversation=conv,
        sender='AI',
        message="⚠️ This ticket has been marked as **Escalated**. A CivicPro support executive has been notified and will review your conversation history in the admin console."
    )

    return JsonResponse({
        'status': 'success',
        'conversation_id': conv.id,
        'message': 'Conversation escalated to human administrator.'
    })


