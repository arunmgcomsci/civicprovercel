"""
CivicPro Forms
All Django forms for user registration, profile management, and hiring.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, HireRequest, Review


class WorkerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'Email Address'
        })
    )
    phone = forms.CharField(
        max_length=15, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': '+91 XXXXX XXXXX'
        })
    )
    skill_category = forms.ChoiceField(
        choices=[('', '-- Select Skill --')] + UserProfile.SKILL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all'
        })
    )
    daily_rate = forms.DecimalField(
        max_digits=8, decimal_places=2, required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'Daily Rate (₹)'
        })
    )
    experience_years = forms.IntegerField(
        min_value=0, max_value=50, required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'Years of Experience'
        })
    )
    location_name = forms.CharField(
        max_length=200, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'Area / Locality, City'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_cls = 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all'
        for field_name in ['username', 'password1', 'password2']:
            self.fields[field_name].widget.attrs.update({
                'class': input_cls,
                'placeholder': {
                    'username': 'Choose a Username',
                    'password1': 'Create Password',
                    'password2': 'Confirm Password',
                }.get(field_name, '')
            })
            self.fields[field_name].help_text = ''


class EmployerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'Email Address'
        })
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': '+91 XXXXX XXXXX'
        })
    )
    company_name = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
            'placeholder': 'Company / Organization (Optional)'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_cls = 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all'
        for field_name in ['username', 'password1', 'password2']:
            self.fields[field_name].widget.attrs.update({
                'class': input_cls,
                'placeholder': {
                    'username': 'Choose a Username',
                    'password1': 'Create Password',
                    'password2': 'Confirm Password',
                }.get(field_name, '')
            })
            self.fields[field_name].help_text = ''


class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'phone', 'skill_category', 'daily_rate', 'experience_years',
            'bio', 'location_name', 'latitude', 'longitude',
            'is_available', 'profile_photo', 'medical_conditions'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'placeholder': '+91 XXXXX XXXXX'
            }),
            'skill_category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all'
            }),
            'daily_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'placeholder': 'Daily Wage (₹)'
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'min': '0', 'max': '50'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'rows': 4,
                'placeholder': 'Tell employers about your skills and work experience...'
            }),
            'location_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'placeholder': 'e.g. Koramangala, Bangalore'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-slate-300 bg-white text-blue-600 focus:ring-blue-500'
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700'
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'rows': 3,
                'placeholder': 'List any critical pre-existing medical conditions (e.g., Asthma, Diabetes, Allergies, Heart Condition...)'
            }),
        }



class HireRequestForm(forms.ModelForm):
    class Meta:
        model = HireRequest
        fields = ['job_description', 'work_date', 'work_location']
        widgets = {
            'job_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'rows': 4,
                'placeholder': 'Describe the work needed in detail...'
            }),
            'work_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'type': 'date'
            }),
            'work_location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'placeholder': 'Work site address'
            }),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all',
                'rows': 4,
                'placeholder': 'Share your experience working with this professional...'
            }),
        }


class WorkerSearchForm(forms.Form):
    RADIUS_CHOICES = [
        (2, '2 km'),
        (5, '5 km'),
        (10, '10 km'),
        (25, '25 km'),
        (50, '50 km'),
        (100, 'Any Distance'),
    ]
    skill = forms.ChoiceField(
        choices=[('', 'All Skills')] + UserProfile.SKILL_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all text-sm'
        })
    )
    radius = forms.IntegerField(
        required=False, initial=10,
        widget=forms.HiddenInput()
    )
    lat = forms.FloatField(required=False, widget=forms.HiddenInput())
    lng = forms.FloatField(required=False, widget=forms.HiddenInput())
