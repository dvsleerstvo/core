from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User as AuthUser
from demonlist.models import Level, User, Victor, DiscordLink, RecordRequest

class SubmitRecordValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.auth_user = AuthUser.objects.create_user(username="testuser", password="password")
        self.gd_user = User.objects.create(username="TestPlayer")
        DiscordLink.objects.create(auth_user=self.auth_user, gd_user=self.gd_user)
        
        self.level = Level.objects.create(
            name="Test Level",
            place=1,
            list_percentage_pc=60,
            list_percentage_mobile=50
        )
        self.client.login(username="testuser", password="password")

    def test_submit_below_list_percentage_pc(self):
        response = self.client.post(reverse('record-request-list'), {
            'level': self.level.id,
            'progress': 59,
            'video': 'https://youtube.com/watch?v=123',
            'device': 'PC'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("below minimum", response.json().get("error", ""))
        self.assertFalse(RecordRequest.objects.filter(user=self.gd_user, level=self.level).exists())

    def test_submit_at_list_percentage_pc(self):
        response = self.client.post(reverse('record-request-list'), {
            'level': self.level.id,
            'progress': 60,
            'video': 'https://youtube.com/watch?v=123',
            'device': 'PC'
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(RecordRequest.objects.filter(user=self.gd_user, level=self.level, progress=60).exists())

    def test_submit_duplicate_victor(self):
        Victor.objects.create(username=self.gd_user, level=self.level, progress=100, device='PC')
        response = self.client.post(reverse('record-request-list'), {
            'level': self.level.id,
            'progress': 100,
            'video': 'https://youtube.com/watch?v=123',
            'device': 'PC'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Higher or equal record already exists", response.json().get("error", ""))
        self.assertEqual(RecordRequest.objects.filter(user=self.gd_user, level=self.level).count(), 0)

    def test_submit_lower_than_existing_victor(self):
        Victor.objects.create(username=self.gd_user, level=self.level, progress=100, device='PC')
        response = self.client.post(reverse('record-request-list'), {
            'level': self.level.id,
            'progress': 90,
            'video': 'https://youtube.com/watch?v=123',
            'device': 'PC'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Higher or equal record already exists", response.json().get("error", ""))

    def test_submit_duplicate_pending_request(self):
        RecordRequest.objects.create(
            user=self.gd_user, level=self.level, progress=80, 
            video='https://youtube.com/watch?v=1', device='PC', status='pending'
        )
        response = self.client.post(reverse('record-request-list'), {
            'level': self.level.id,
            'progress': 80,
            'video': 'https://youtube.com/watch?v=2',
            'device': 'PC'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("already pending", response.json().get("error", ""))
        self.assertEqual(RecordRequest.objects.filter(user=self.gd_user, level=self.level).count(), 1)

    def test_submit_higher_than_pending_request_is_allowed(self):
        RecordRequest.objects.create(
            user=self.gd_user, level=self.level, progress=80, 
            video='https://youtube.com/watch?v=1', device='PC', status='pending'
        )
        response = self.client.post(reverse('record-request-list'), {
            'level': self.level.id,
            'progress': 90,
            'video': 'https://youtube.com/watch?v=2',
            'device': 'PC'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RecordRequest.objects.filter(user=self.gd_user, level=self.level).count(), 2)

    def test_submit_after_rejected_request_is_allowed(self):
        RecordRequest.objects.create(
            user=self.gd_user, level=self.level, progress=100, 
            video='https://youtube.com/watch?v=1', device='PC', status='rejected'
        )
        response = self.client.post(reverse('record-request-list'), {
            'level': self.level.id,
            'progress': 100,
            'video': 'https://youtube.com/watch?v=2',
            'device': 'PC'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RecordRequest.objects.filter(user=self.gd_user, level=self.level, status='pending').count(), 1)
