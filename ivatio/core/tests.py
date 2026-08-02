from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import UserProfile, HireRequest, Review
from core.views import haversine_distance, get_workers_with_distance
from datetime import date


class CivicProModelTests(TestCase):
    def setUp(self):
        self.worker_user = User.objects.create_user(
            username='test_worker',
            first_name='Test',
            last_name='Worker',
            email='worker@test.com',
            password='password123'
        )
        self.worker_profile = UserProfile.objects.create(
            user=self.worker_user,
            role='WORKER',
            phone='+91 9999988888',
            skill_category='ELECTRICIAN',
            daily_rate=600,
            experience_years=5,
            location_name='Indiranagar, Bangalore',
            latitude=12.9784,
            longitude=77.6408,
            is_available=True,
            is_verified=True,
        )

        self.employer_user = User.objects.create_user(
            username='test_employer',
            first_name='Test',
            last_name='Employer',
            email='employer@test.com',
            password='password123'
        )
        self.employer_profile = UserProfile.objects.create(
            user=self.employer_user,
            role='EMPLOYER',
            phone='+91 8888877777',
        )

    def test_haversine_distance_calculation(self):
        # Distance between Bangalore Center (12.9716, 77.5946) and Indiranagar (12.9784, 77.6408) is ~5.0 km
        dist = haversine_distance(12.9716, 77.5946, 12.9784, 77.6408)
        self.assertAlmostEqual(dist, 5.06, delta=0.5)

    def test_auto_geocoding(self):
        user = User.objects.create_user(
            username='palakkad_worker',
            password='password123'
        )
        profile = UserProfile.objects.create(
            user=user,
            role='WORKER',
            location_name='palakkad'
        )
        self.assertIsNotNone(profile.latitude)
        self.assertIsNotNone(profile.longitude)
        self.assertAlmostEqual(profile.latitude, 10.7699, delta=0.5)
        self.assertAlmostEqual(profile.longitude, 76.6496, delta=0.5)

    def test_get_workers_with_distance(self):
        workers = get_workers_with_distance(12.9716, 77.5946, skill='ELECTRICIAN', radius=10)
        self.assertEqual(len(workers), 1)
        self.assertEqual(workers[0]['worker'], self.worker_profile)
        self.assertTrue(workers[0]['distance'] < 10)

    def test_hire_request_lifecycle_and_review(self):
        # 1. Create hire request
        hire_req = HireRequest.objects.create(
            employer=self.employer_user,
            worker=self.worker_profile,
            job_description='Fix main circuit breaker and lights.',
            work_date=date.today(),
            work_location='Indiranagar 100ft road',
            status='PENDING'
        )
        self.assertEqual(hire_req.status, 'PENDING')
        self.assertFalse(hire_req.can_review())

        # 2. Worker accepts
        hire_req.status = 'ACCEPTED'
        hire_req.save()
        self.assertEqual(hire_req.status, 'ACCEPTED')
        self.assertFalse(hire_req.can_review())

        # 3. Mark completed
        hire_req.status = 'COMPLETED'
        hire_req.save()
        self.assertEqual(hire_req.status, 'COMPLETED')
        self.assertTrue(hire_req.can_review())

        # 4. Employer leaves review
        review = Review.objects.create(
            hire_request=hire_req,
            worker=self.worker_profile,
            employer=self.employer_user,
            rating=5,
            comment='Excellent electrical work!'
        )
        self.assertEqual(self.worker_profile.avg_rating(), 5.0)
        self.assertEqual(self.worker_profile.total_jobs(), 1)
        # Cannot review twice
        self.assertFalse(hire_req.can_review())


class CivicProViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.worker_user = User.objects.create_user(
            username='worker_bob',
            first_name='Bob',
            password='password123'
        )
        self.worker_profile = UserProfile.objects.create(
            user=self.worker_user,
            role='WORKER',
            skill_category='PLUMBER',
            daily_rate=500,
            latitude=12.9352,
            longitude=77.6245,
            is_available=True,
        )

        self.employer_user = User.objects.create_user(
            username='emp_alice',
            first_name='Alice',
            password='password123'
        )
        self.employer_profile = UserProfile.objects.create(
            user=self.employer_user,
            role='EMPLOYER',
        )

    def test_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CivicPro')
        self.assertContains(response, 'Hire')

    def test_search_page(self):
        self.client.login(username='emp_alice', password='password123')
        response = self.client.get('/search/?lat=12.9350&lng=77.6240&radius=10')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bob')

    def test_worker_availability_toggle_api(self):
        self.client.login(username='worker_bob', password='password123')
        response = self.client.post('/worker/toggle-availability/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['is_available'], False)
        self.worker_profile.refresh_from_db()
        self.assertFalse(self.worker_profile.is_available)
