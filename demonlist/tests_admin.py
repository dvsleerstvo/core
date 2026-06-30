from django.test import TestCase, Client
from django.contrib.auth.models import User as AuthUser
from django.urls import reverse
from .models import Level, User, Victor, RecordRequest

class DemonlistAdminTest(TestCase):
    def setUp(self):
        self.admin_user = AuthUser.objects.create_superuser(username="admin", password="password", email="admin@test.com")
        self.client = Client()
        self.client.login(username="admin", password="password")
        
        self.level = Level.objects.create(name="Admin Level", place=1, level_id=999)
        self.user = User.objects.create(username="Admin Player")
        self.victor = Victor.objects.create(username=self.user, level=self.level, progress=100, device="Mobile")

    def test_admin_update_devicetype_pc(self):
        # Тестируем действие "Заменить устройства на ПК"
        data = {
            'action': 'update_devicetype_pc',
            '_selected_action': [self.victor.id]
        }
        url = reverse('admin:demonlist_victor_changelist')
        self.client.post(url, data)
        
        self.victor.refresh_from_db()
        self.assertEqual(self.victor.device, "PC")

    def test_admin_record_request_approval(self):
        # Создаем заявку
        request = RecordRequest.objects.create(
            user=self.user,
            level=self.level,
            progress=100,
            video="https://youtube.com/watch?v=admin",
            device="PC",
            status="pending"
        )
        
        # Меняем статус через админку (имитируем сохранение модели)
        url = reverse('admin:demonlist_recordrequest_change', args=(request.id,))
        data = {
            'user': self.user.id,
            'level': self.level.id,
            'progress': 100,
            'video': "https://youtube.com/watch?v=admin",
            'device': "PC",
            'status': 'approved',
            '_save': 'Save'
        }
        self.client.post(url, data)
        
        # Проверяем, что создался Victor (логика в save_model)
        self.assertTrue(Victor.objects.filter(username=self.user, level=self.level, device="PC").exists())

    def test_admin_custom_urls(self):
        # Проверяем доступность кастомного URL обновления очков
        url = reverse('admin:update-scores')
        response = self.client.get(url)
        # Должен произойти редирект обратно на список уровней
        self.assertEqual(response.status_code, 302)
        
    def test_admin_user_update_all_scores(self):
        url = reverse('admin:update_all_scores')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
