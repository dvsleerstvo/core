from django.test import TestCase
from django.contrib.auth.models import User as AuthUser
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Level, User, Victor, RecordRequest, DiscordLink
from .selectors import get_user_rank_with_count

class DemonlistLogicTest(TestCase):
    def setUp(self):
        self.level1 = Level.objects.create(name="Level 1", place=1, level_id=101, completion_points_pc=100)
        self.level2 = Level.objects.create(name="Level 2", place=2, level_id=102, completion_points_pc=50)
        self.user1 = User.objects.create(username="Player 1", score_pc=0)
        self.user2 = User.objects.create(username="Player 2", score_pc=0)

    def test_rank_calculation(self):
        # Добавляем победу первому игроку на сложном уровне
        Victor.objects.create(username=self.user1, level=self.level1, progress=100, device='PC')
        self.user1.score_pc = 100
        self.user1.save()
        
        # Добавляем победу второму на легком
        Victor.objects.create(username=self.user2, level=self.level2, progress=100, device='PC')
        self.user2.score_pc = 50
        self.user2.save()

        self.assertEqual(get_user_rank_with_count(self.user1.id, 'PC'), 1)
        self.assertEqual(get_user_rank_with_count(self.user2.id, 'PC'), 2)

    def test_first_victor_uniqueness(self):
        v1 = Victor.objects.create(username=self.user1, level=self.level1, progress=100, device='PC', is_first_victor=True)
        v2 = Victor.objects.create(username=self.user2, level=self.level1, progress=100, device='PC', is_first_victor=True)
        
        v1.refresh_from_db()
        self.assertFalse(v1.is_first_victor)
        self.assertTrue(v2.is_first_victor)

class DemonlistAPITest(APITestCase):
    def setUp(self):
        self.level = Level.objects.create(name="Acheron", place=1, level_id=123, completion_points_pc=100)
        self.auth_user = AuthUser.objects.create_user(username="testuser", password="password")
        self.gd_user = User.objects.create(username="GDPlayer")
        self.link = DiscordLink.objects.create(auth_user=self.auth_user, gd_user=self.gd_user)

    def test_get_levels(self):
        # Уровень должен быть в списке только если есть виктор (наша логика)
        Victor.objects.create(username=self.gd_user, level=self.level, progress=100, device='PC')
        response = self.client.get('/api/v2/levels/?device=pc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)

    def test_submit_record_auth(self):
        self.client.force_authenticate(user=self.auth_user)
        data = {
            "level": self.level.id,
            "progress": 100,
            "video": "https://youtube.com/watch?v=123",
            "device": "PC"
        }
        response = self.client.post('/api/v2/record-requests/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RecordRequest.objects.count(), 1)
