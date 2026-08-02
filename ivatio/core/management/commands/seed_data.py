"""
CivicPro Seed Data Management Command
Creates realistic demo data with workers across Bangalore for testing.
Run with: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, HireRequest, Review
from datetime import date, timedelta
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Seeds CivicPro with realistic demo data including workers, employers, and hire requests.'

    # Bangalore area worker data with realistic GPS coordinates
    WORKERS = [
        {
            'username': 'rajesh_elec',
            'first_name': 'Rajesh',
            'last_name': 'Kumar',
            'email': 'rajesh@civicpro.in',
            'skill_category': 'ELECTRICIAN',
            'daily_rate': 750,
            'experience_years': 8,
            'location_name': 'Koramangala, Bangalore',
            'lat': 12.9352,
            'lng': 77.6245,
            'is_available': True,
            'is_verified': True,
            'bio': 'Expert electrician with 8 years experience in residential and commercial wiring, switchboards, and solar panel installations. Licensed contractor.',
            'phone': '+91 9845012345',
        },
        {
            'username': 'suresh_plumber',
            'first_name': 'Suresh',
            'last_name': 'Rao',
            'email': 'suresh@civicpro.in',
            'skill_category': 'PLUMBER',
            'daily_rate': 650,
            'experience_years': 12,
            'location_name': 'Indiranagar, Bangalore',
            'lat': 12.9784,
            'lng': 77.6408,
            'is_available': True,
            'is_verified': True,
            'bio': 'Senior plumber specializing in bathroom fittings, pipeline repair, water heater installation, and drainage systems. Available 7 days a week.',
            'phone': '+91 9867891234',
        },
        {
            'username': 'vinod_driver',
            'first_name': 'Vinod',
            'last_name': 'Nair',
            'email': 'vinod@civicpro.in',
            'skill_category': 'DRIVER',
            'daily_rate': 600,
            'experience_years': 15,
            'location_name': 'Whitefield, Bangalore',
            'lat': 12.9698,
            'lng': 77.7499,
            'is_available': True,
            'is_verified': True,
            'bio': 'Professional driver with 15 years experience. Clean record, multi-vehicle trained (Car, SUV, Tempo). Available for outstation trips too.',
            'phone': '+91 9834567890',
        },
        {
            'username': 'mohan_carp',
            'first_name': 'Mohan',
            'last_name': 'Das',
            'email': 'mohan@civicpro.in',
            'skill_category': 'CARPENTER',
            'daily_rate': 700,
            'experience_years': 10,
            'location_name': 'HSR Layout, Bangalore',
            'lat': 12.9116,
            'lng': 77.6474,
            'is_available': True,
            'is_verified': False,
            'bio': 'Skilled carpenter for furniture making, modular kitchen installation, door frames, windows, and woodwork. Custom designs at affordable rates.',
            'phone': '+91 9756234567',
        },
        {
            'username': 'ganesh_painter',
            'first_name': 'Ganesh',
            'last_name': 'Reddy',
            'email': 'ganesh@civicpro.in',
            'skill_category': 'PAINTER',
            'daily_rate': 550,
            'experience_years': 6,
            'location_name': 'BTM Layout, Bangalore',
            'lat': 12.9166,
            'lng': 77.6101,
            'is_available': True,
            'is_verified': True,
            'bio': 'Interior and exterior painter. Expert in wall textures, waterproofing, wood polish, and decorative finishes. Materials can be arranged.',
            'phone': '+91 9823456789',
        },
        {
            'username': 'ramu_helper',
            'first_name': 'Ramu',
            'last_name': 'Shankar',
            'email': 'ramu@civicpro.in',
            'skill_category': 'HELPER',
            'daily_rate': 450,
            'experience_years': 4,
            'location_name': 'Marathahalli, Bangalore',
            'lat': 12.9591,
            'lng': 77.6974,
            'is_available': True,
            'is_verified': False,
            'bio': 'Hardworking construction helper. Experienced in site work, material handling, digging, and general labor. Punctual and reliable.',
            'phone': '+91 9712345678',
        },
        {
            'username': 'anand_mason',
            'first_name': 'Anand',
            'last_name': 'Pillai',
            'email': 'anand@civicpro.in',
            'skill_category': 'MASON',
            'daily_rate': 800,
            'experience_years': 14,
            'location_name': 'Jayanagar, Bangalore',
            'lat': 12.9249,
            'lng': 77.5831,
            'is_available': False,  # Busy
            'is_verified': True,
            'bio': 'Expert mason with 14 years in bricklaying, plastering, tiling, and concrete work. Can handle both residential and commercial projects.',
            'phone': '+91 9645678901',
        },
        {
            'username': 'krishna_welder',
            'first_name': 'Krishna',
            'last_name': 'Murthy',
            'email': 'krishna@civicpro.in',
            'skill_category': 'WELDER',
            'daily_rate': 900,
            'experience_years': 18,
            'location_name': 'Electronic City, Bangalore',
            'lat': 12.8452,
            'lng': 77.6602,
            'is_available': True,
            'is_verified': True,
            'bio': 'Certified welder (Arc, MIG, TIG). Expert in structural steel, gates, grills, railings, and metal fabrication for industrial projects.',
            'phone': '+91 9567890123',
        },
        {
            'username': 'shiva_gardener',
            'first_name': 'Shiva',
            'last_name': 'Prasad',
            'email': 'shiva@civicpro.in',
            'skill_category': 'GARDENER',
            'daily_rate': 500,
            'experience_years': 7,
            'location_name': 'Sadashivanagar, Bangalore',
            'lat': 13.0082,
            'lng': 77.5789,
            'is_available': True,
            'is_verified': False,
            'bio': 'Professional gardener with expertise in landscape design, tree trimming, lawn maintenance, and organic gardening techniques.',
            'phone': '+91 9478901234',
        },
        {
            'username': 'priya_cleaner',
            'first_name': 'Priya',
            'last_name': 'Devi',
            'email': 'priya@civicpro.in',
            'skill_category': 'CLEANER',
            'daily_rate': 400,
            'experience_years': 3,
            'location_name': 'Malleshwaram, Bangalore',
            'lat': 13.0035,
            'lng': 77.5657,
            'is_available': True,
            'is_verified': True,
            'bio': 'Professional house cleaner specializing in deep cleaning, move-in/move-out cleaning, and post-renovation cleaning. Brings own equipment.',
            'phone': '+91 9389012345',
        },
        {
            'username': 'arun_elec2',
            'first_name': 'Arun',
            'last_name': 'Babu',
            'email': 'arun@civicpro.in',
            'skill_category': 'ELECTRICIAN',
            'daily_rate': 680,
            'experience_years': 5,
            'location_name': 'Yelahanka, Bangalore',
            'lat': 13.1007,
            'lng': 77.5963,
            'is_available': True,
            'is_verified': True,
            'bio': 'Residential electrician specializing in home automation, CCTV installation, inverter and UPS setup, and rewiring.',
            'phone': '+91 9290123456',
        },
        {
            'username': 'deepak_plumb2',
            'first_name': 'Deepak',
            'last_name': 'Shetty',
            'email': 'deepak@civicpro.in',
            'skill_category': 'PLUMBER',
            'daily_rate': 600,
            'experience_years': 9,
            'location_name': 'Banashankari, Bangalore',
            'lat': 12.9207,
            'lng': 77.5464,
            'is_available': True,
            'is_verified': False,
            'bio': 'Plumbing expert for new installations, bore well, water tank cleaning, and pipe replacement. Same-day service available.',
            'phone': '+91 9201234567',
        },
        {
            'username': 'ravi_driver2',
            'first_name': 'Ravi',
            'last_name': 'Shankar',
            'email': 'ravi@civicpro.in',
            'skill_category': 'DRIVER',
            'daily_rate': 550,
            'experience_years': 8,
            'location_name': 'JP Nagar, Bangalore',
            'lat': 12.9006,
            'lng': 77.5821,
            'is_available': False,  # Busy
            'is_verified': True,
            'bio': 'Experienced car driver for daily commute, airport transfers, and outstation travel. Familiar with all Bangalore routes.',
            'phone': '+91 9112345678',
        },
        {
            'username': 'kumar_carp2',
            'first_name': 'Kumar',
            'last_name': 'Naidu',
            'email': 'kumar@civicpro.in',
            'skill_category': 'CARPENTER',
            'daily_rate': 650,
            'experience_years': 7,
            'location_name': 'Rajajinagar, Bangalore',
            'lat': 12.9901,
            'lng': 77.5530,
            'is_available': True,
            'is_verified': True,
            'bio': 'Furniture carpenter with skills in bedroom sets, wardrobes, kitchen cabinets, and office furniture. Quality work guaranteed.',
            'phone': '+91 9023456789',
        },
    ]

    EMPLOYERS = [
        {
            'username': 'rahul_employer',
            'first_name': 'Rahul',
            'last_name': 'Mehta',
            'email': 'rahul@civicpro.in',
            'phone': '+91 9876543210',
        },
        {
            'username': 'ananya_emp',
            'first_name': 'Ananya',
            'last_name': 'Singh',
            'email': 'ananya@civicpro.in',
            'phone': '+91 9765432109',
        },
        {
            'username': 'vikram_emp',
            'first_name': 'Vikram',
            'last_name': 'Patel',
            'email': 'vikram@civicpro.in',
            'phone': '+91 9654321098',
        },
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🌱 Seeding CivicPro demo data...'))

        # Create superuser
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@civicpro.in',
                password='admin123',
                first_name='Admin',
                last_name='CivicPro'
            )
            UserProfile.objects.create(
                user=admin_user,
                role='ADMIN',
                phone='+91 9999999999',
                location_name='Bangalore, Karnataka',
                is_verified=True,
            )
            self.stdout.write(self.style.SUCCESS('✅ Admin user created (admin / admin123)'))

        # Create Workers
        created_workers = []
        for data in self.WORKERS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                }
            )
            if created:
                user.set_password('worker123')
                user.save()

            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'WORKER',
                    'phone': data['phone'],
                    'skill_category': data['skill_category'],
                    'daily_rate': data['daily_rate'],
                    'experience_years': data['experience_years'],
                    'location_name': data['location_name'],
                    'latitude': data['lat'],
                    'longitude': data['lng'],
                    'is_available': data['is_available'],
                    'is_verified': data['is_verified'],
                    'bio': data['bio'],
                }
            )
            created_workers.append(profile)

        self.stdout.write(self.style.SUCCESS(f'✅ {len(self.WORKERS)} workers created (password: worker123)'))

        # Create Employers
        created_employers = []
        for data in self.EMPLOYERS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                }
            )
            if created:
                user.set_password('employer123')
                user.save()

            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'EMPLOYER',
                    'phone': data['phone'],
                }
            )
            created_employers.append(user)

        self.stdout.write(self.style.SUCCESS(f'✅ {len(self.EMPLOYERS)} employers created (password: employer123)'))

        # Create Demo Hire Requests & Reviews
        hire_scenarios = [
            {
                'employer_idx': 0,
                'worker_idx': 0,  # rajesh_elec
                'description': 'Need complete house rewiring and installation of 5 new power points in the kitchen and living room.',
                'days_ago': 30,
                'status': 'COMPLETED',
                'review': {'rating': 5, 'comment': 'Excellent work! Rajesh was very professional and completed the job on time. Highly recommended!'},
            },
            {
                'employer_idx': 0,
                'worker_idx': 1,  # suresh_plumber
                'description': 'Bathroom renovation — need new shower fitting, basin, and fix a major pipe leak under the sink.',
                'days_ago': 15,
                'status': 'COMPLETED',
                'review': {'rating': 4, 'comment': 'Good work, fixed all the issues. Slightly delayed but quality was great.'},
            },
            {
                'employer_idx': 1,
                'worker_idx': 4,  # ganesh_painter
                'description': 'Paint 3-bedroom apartment. Interior walls and ceiling. Need texture finish in living room.',
                'days_ago': 10,
                'status': 'ACCEPTED',
                'review': None,
            },
            {
                'employer_idx': 1,
                'worker_idx': 3,  # mohan_carp
                'description': 'Install modular kitchen and build 2 bedroom wardrobes with sliding doors.',
                'days_ago': 5,
                'status': 'PENDING',
                'review': None,
            },
            {
                'employer_idx': 2,
                'worker_idx': 7,  # krishna_welder
                'description': 'Fabricate and install main gate with safety grill. Steel material, manual sliding type.',
                'days_ago': 20,
                'status': 'COMPLETED',
                'review': {'rating': 5, 'comment': 'Krishna did phenomenal work! The gate looks exactly as designed. Very skilled welder.'},
            },
            {
                'employer_idx': 2,
                'worker_idx': 2,  # vinod_driver
                'description': 'Need a full-time driver for a week. Office commute 9am to 6pm, Whitefield to MG Road.',
                'days_ago': 45,
                'status': 'COMPLETED',
                'review': {'rating': 4, 'comment': 'Reliable and punctual driver. Knows all city routes well.'},
            },
            {
                'employer_idx': 0,
                'worker_idx': 5,  # ramu_helper
                'description': 'Need helper for site work. Carrying materials, mixing concrete for foundation work.',
                'days_ago': 3,
                'status': 'PENDING',
                'review': None,
            },
            {
                'employer_idx': 1,
                'worker_idx': 9,  # priya_cleaner
                'description': 'Deep cleaning of 4BHK apartment before moving in. Include kitchen, bathrooms, and all rooms.',
                'days_ago': 8,
                'status': 'ACCEPTED',
                'review': None,
            },
        ]

        for scenario in hire_scenarios:
            employer = created_employers[scenario['employer_idx']]
            worker = created_workers[scenario['worker_idx']]
            work_date = date.today() - timedelta(days=scenario['days_ago'])

            hire_req, created = HireRequest.objects.get_or_create(
                employer=employer,
                worker=worker,
                work_date=work_date,
                defaults={
                    'job_description': scenario['description'],
                    'status': scenario['status'],
                    'work_location': worker.location_name,
                }
            )

            # Create review if applicable
            if created and scenario['review'] and scenario['status'] == 'COMPLETED':
                Review.objects.get_or_create(
                    hire_request=hire_req,
                    employer=employer,
                    defaults={
                        'worker': worker,
                        'rating': scenario['review']['rating'],
                        'comment': scenario['review']['comment'],
                    }
                )

        self.stdout.write(self.style.SUCCESS(f'✅ {len(hire_scenarios)} hire requests & reviews created'))

        # Create demo login accounts
        demo_worker_user, _ = User.objects.get_or_create(
            username='demo_worker',
            defaults={
                'first_name': 'Demo',
                'last_name': 'Worker',
                'email': 'demoworker@civicpro.in',
            }
        )
        demo_worker_user.set_password('civicpro2024')
        demo_worker_user.save()
        UserProfile.objects.get_or_create(
            user=demo_worker_user,
            defaults={
                'role': 'WORKER',
                'phone': '+91 9000000001',
                'skill_category': 'ELECTRICIAN',
                'daily_rate': 650,
                'experience_years': 5,
                'location_name': 'Koramangala, Bangalore',
                'latitude': 12.9352,
                'longitude': 77.6245,
                'is_available': True,
                'bio': 'Demo worker account for testing CivicPro platform.',
            }
        )

        demo_employer_user, _ = User.objects.get_or_create(
            username='demo_employer',
            defaults={
                'first_name': 'Demo',
                'last_name': 'Employer',
                'email': 'demoemployer@civicpro.in',
            }
        )
        demo_employer_user.set_password('civicpro2024')
        demo_employer_user.save()
        UserProfile.objects.get_or_create(
            user=demo_employer_user,
            defaults={
                'role': 'EMPLOYER',
                'phone': '+91 9000000002',
            }
        )

        self.stdout.write(self.style.SUCCESS('✅ Demo accounts created'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
        self.stdout.write(self.style.SUCCESS('🎉 CivicPro seed data created successfully!'))
        self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
        self.stdout.write(f"  Admin:    admin / admin123")
        self.stdout.write(f"  Worker:   demo_worker / civicpro2024")
        self.stdout.write(f"  Employer: demo_employer / civicpro2024")
        self.stdout.write(f"  Workers:  rajesh_elec, suresh_plumber... / worker123")
        self.stdout.write(f"  Employers: rahul_employer, ananya_emp... / employer123")
        self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
