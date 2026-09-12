"""
CivicPro URL Configuration for core app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Authentication
    path('register/worker/', views.register_worker, name='register_worker'),
    path('register/employer/', views.register_employer, name='register_employer'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Worker Module
    path('worker/profile/setup/', views.worker_profile_setup, name='worker_profile_setup'),
    path('worker/dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('worker/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('worker/hire-request/<int:pk>/respond/', views.respond_hire_request, name='respond_hire_request'),

    # Employer Module
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('search/', views.search_workers, name='search_workers'),
    path('worker/<int:pk>/', views.worker_detail, name='worker_detail'),
    path('worker/<int:worker_pk>/hire/', views.send_hire_request, name='send_hire_request'),
    path('hire/<int:pk>/complete/', views.mark_hire_completed, name='mark_hire_completed'),

    # Reviews
    path('review/<int:hire_request_pk>/submit/', views.submit_review, name='submit_review'),

    # Emergency Services
    path('emergency/', views.emergency_view, name='emergency_view'),
    path('emergency/trigger/', views.trigger_emergency, name='trigger_emergency'),
    path('emergency/end/', views.end_emergency, name='end_emergency'),
    path('emergency/update-status/', views.update_emergency_status, name='update_emergency_status'),
    path('emergency/active/', views.get_active_emergency, name='get_active_emergency'),


    # API
    path('api/workers/', views.api_workers_nearby, name='api_workers_nearby'),
]

