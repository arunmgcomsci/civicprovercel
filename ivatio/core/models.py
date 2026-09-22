"""
CivicPro Core Models
Database models for the Worker-Employer hiring platform.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import urllib.request
import urllib.parse
import json

def geocode_location(location_name):
    """
    Geocodes a location name using Nominatim OpenStreetMap API.
    Returns (latitude, longitude) or (None, None) on failure.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location_name)}&format=json&limit=1"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'CivicProApp/1.0 (contact: admin@civicpro.in)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Geocoding error: {e}")

    # Fallbacks based on common search keywords
    loc_lower = location_name.lower().strip()
    if 'kochi' in loc_lower or 'cochin' in loc_lower or 'ernakulam' in loc_lower:
        return 9.9816, 76.2999
    if 'thrissur' in loc_lower or 'trichur' in loc_lower:
        return 10.5276, 76.2144
    if 'shornur' in loc_lower or 'shoranur' in loc_lower:
        return 10.7621, 76.2796
    if 'palakkad' in loc_lower:
        return 10.7867, 76.6548
    if 'calicut' in loc_lower or 'kozhikode' in loc_lower:
        return 11.2588, 75.7804
    if 'trivandrum' in loc_lower or 'thiruvananthapuram' in loc_lower:
        return 8.5241, 76.9366
    if 'kollam' in loc_lower or 'quilon' in loc_lower:
        return 8.8932, 76.6141
    if 'alappuzha' in loc_lower or 'alleppey' in loc_lower:
        return 9.4981, 76.3388
    if 'kottayam' in loc_lower:
        return 9.5916, 76.5222
    if 'kannur' in loc_lower:
        return 11.8745, 75.3704
    if 'malappuram' in loc_lower:
        return 11.0510, 76.0711
    if 'wayanad' in loc_lower or 'kalpetta' in loc_lower:
        return 11.6050, 76.0828
    if 'kasaragod' in loc_lower:
        return 12.4996, 74.9869
    if 'bangalore' in loc_lower or 'bengaluru' in loc_lower:
        return 12.9716, 77.5946
    if 'koramangala' in loc_lower:
        return 12.9352, 77.6245
    if 'indiranagar' in loc_lower:
        return 12.9784, 77.6408
    if 'whitefield' in loc_lower:
        return 12.9698, 77.7499
    if 'hsr' in loc_lower:
        return 12.9116, 77.6474
    if 'chennai' in loc_lower or 'madras' in loc_lower:
        return 13.0827, 80.2707
    if 'mumbai' in loc_lower or 'bombay' in loc_lower:
        return 19.0760, 72.8777
    if 'delhi' in loc_lower:
        return 28.6139, 77.2090
    if 'hyderabad' in loc_lower:
        return 17.3850, 78.4867
    if 'pune' in loc_lower:
        return 18.5204, 73.8567
    if 'kolkata' in loc_lower or 'calcutta' in loc_lower:
        return 22.5726, 88.3639

    return None, None


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('WORKER', 'Worker'),
        ('EMPLOYER', 'Employer'),
        ('ADMIN', 'Admin'),
    ]
    SKILL_CHOICES = [
        ('ELECTRICIAN', 'Electrician'),
        ('PLUMBER', 'Plumber'),
        ('DRIVER', 'Driver'),
        ('CARPENTER', 'Carpenter'),
        ('PAINTER', 'Painter'),
        ('HELPER', 'Construction Helper'),
        ('MASON', 'Mason'),
        ('WELDER', 'Welder'),
        ('GARDENER', 'Gardener'),
        ('CLEANER', 'House Cleaner'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='WORKER')
    phone = models.CharField(max_length=15, blank=True)
    skill_category = models.CharField(max_length=20, choices=SKILL_CHOICES, blank=True, null=True)
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, default='')
    is_available = models.BooleanField(default=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    is_verified = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    medical_conditions = models.TextField(blank=True, default='', verbose_name="Medical Alerts / Pre-existing Conditions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role})"

    def get_skill_display_icon(self):
        icons = {
            'ELECTRICIAN': '⚡',
            'PLUMBER': '🔧',
            'DRIVER': '🚗',
            'CARPENTER': '🪚',
            'PAINTER': '🖌️',
            'HELPER': '👷',
            'MASON': '🧱',
            'WELDER': '🔥',
            'GARDENER': '🌿',
            'CLEANER': '🧹',
        }
        return icons.get(self.skill_category, '👤')

    def avg_rating(self):
        reviews = self.reviews_received.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None

    def total_jobs(self):
        return self.hire_requests_received.filter(status='COMPLETED').count()

    def save(self, *args, **kwargs):
        if self.location_name and (self.latitude is None or self.longitude is None):
            lat, lng = geocode_location(self.location_name)
            if lat is not None and lng is not None:
                self.latitude = lat
                self.longitude = lng
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class HireRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    employer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='hire_requests_sent'
    )
    worker = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='hire_requests_received'
    )
    job_description = models.TextField()
    work_date = models.DateField()
    work_location = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    employer_notes = models.TextField(blank=True)
    worker_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Hire: {self.employer.username} → {self.worker.user.username} ({self.status})"

    def can_review(self):
        """Check if employer can leave a review for this hire"""
        return (
            self.status == 'COMPLETED'
            and not Review.objects.filter(
                hire_request=self,
                employer=self.employer
            ).exists()
        )

    class Meta:
        verbose_name = 'Hire Request'
        verbose_name_plural = 'Hire Requests'
        ordering = ['-created_at']


class Review(models.Model):
    worker = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='reviews_received'
    )
    employer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews_given'
    )
    hire_request = models.OneToOneField(
        HireRequest, on_delete=models.CASCADE, related_name='review',
        null=True, blank=True
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.employer.username} for {self.worker.user.username}: {self.rating}★"

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['hire_request', 'employer']


class WorkerAvailabilityLog(models.Model):
    """Track when workers toggle their availability"""
    worker = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='availability_logs')
    became_available = models.BooleanField()
    logged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Available" if self.became_available else "Busy"
        return f"{self.worker} → {status} at {self.logged_at}"


class EmergencyCall(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ENDED', 'Ended'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_calls')
    service_type = models.CharField(max_length=50)  # e.g. 'AMBULANCE', 'FIRE FORCE', etc.
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    condition = models.CharField(max_length=100, default='Panic / Urgent')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Emergency: {self.user.username} - {self.service_type} ({self.status})"


class SupportConversation(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('RESOLVED', 'Resolved'),
        ('ESCALATED', 'Escalated to Human Admin'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_conversations')
    session_key = models.CharField(max_length=64, db_index=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='OPEN')
    subject = models.CharField(max_length=200, default='General Inquiry')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_name = self.user.username if self.user else f"Guest ({self.session_key[:8] if self.session_key else 'Anonymous'})"
        return f"Support #{self.id}: {user_name} - {self.subject} ({self.status})"

    class Meta:
        verbose_name = 'Support Conversation'
        verbose_name_plural = 'Support Conversations'
        ordering = ['-updated_at']


class SupportMessage(models.Model):
    SENDER_CHOICES = [
        ('USER', 'User / Visitor'),
        ('AI', 'AI Support Executive'),
        ('ADMIN', 'Human Admin'),
    ]

    conversation = models.ForeignKey(SupportConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES, default='USER')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.sender}] #{self.conversation.id}: {self.message[:40]}"

    class Meta:
        verbose_name = 'Support Message'
        verbose_name_plural = 'Support Messages'
        ordering = ['created_at']

