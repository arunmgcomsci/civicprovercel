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
    loc_lower = location_name.lower()
    if 'kochi' in loc_lower or 'cochin' in loc_lower:
        return 9.9592, 76.3243
    if 'palakkad' in loc_lower:
        return 10.7699, 76.6496
    if 'bangalore' in loc_lower or 'bengaluru' in loc_lower:
        return 12.9716, 77.5946

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
