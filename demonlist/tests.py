from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User as AuthUser
from django.core.cache import cache
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from demonlist.models import Level, User, Victor, DiscordLink, RecordRequest
from demonlist.selectors import get_user_rank_with_count, get_level_rank
from demonlist.services import update_user_hardest, get_unique_level_victors


class ModelTests(TestCase):
    def setUp(self):
        self.level = Level.objects.create(
            level_id=123,
            global_demonlist_id=1,
            name="Bloodbath",
            place=1,
            video="https://youtu.be/dQw4w9WgXcQ",
            completion_points_pc=100.0,
            completion_points_mobile=120.0
        )
        self.user = User.objects.create(
            username="Riot",
            global_demonlist_user_id=1,
            region="RU",
            score_pc=100.0,
            score_mobile=0.0
        )
        self.auth_user = AuthUser.objects.create_user(username="testuser", password="password")

    def test_level_str(self):
        self.assertEqual(str(self.level), "Bloodbath")

    def test_embed_url_youtu_be(self):
        self.assertEqual(self.level.embed_url, "https://www.youtube.com/embed/dQw4w9WgXcQ")

    def test_embed_url_watch_v(self):
        self.level.video = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.level.save()
        self.assertEqual(self.level.embed_url, "https://www.youtube.com/embed/dQw4w9WgXcQ")

    def test_user_str(self):
        self.assertEqual(str(self.user), "Riot")

    def test_victor_str(self):
        victor = Victor.objects.create(username=self.user, level=self.level, progress=100, device="PC")
        self.assertEqual(str(victor), "Bloodbath - Riot")

    def test_discord_link_str(self):
        link = DiscordLink.objects.create(auth_user=self.auth_user, gd_user=self.user)
        self.assertEqual(str(link), "testuser <-> Riot")

    def test_record_request_str(self):
        req = RecordRequest.objects.create(
            user=self.user, level=self.level, progress=100, video="https://youtube.com", device="PC"
        )
        self.assertEqual(str(req), "[В ожидании] Riot - Bloodbath (100%)")


class SelectorTests(TestCase):
    def setUp(self):
        # Назначаем уровни с очками, чтобы сигналы не обнуляли счет при создании Victor
        self.level1 = Level.objects.create(place=1, name="Level 1", completion_points_pc=500,
                                           completion_points_mobile=100)
        self.level2 = Level.objects.create(place=2, name="Level 2", completion_points_pc=300,
                                           completion_points_mobile=200)

        self.user1 = User.objects.create(username="Player1", score_pc=500, score_mobile=100)
        self.user2 = User.objects.create(username="Player2", score_pc=300, score_mobile=200)

        Victor.objects.create(username=self.user1, level=self.level1, progress=100, device="PC")
        Victor.objects.create(username=self.user2, level=self.level2, progress=100, device="Mobile")

    def test_get_user_rank_with_count(self):
        rank_pc_user1 = get_user_rank_with_count(self.user1.id, "PC")
        rank_pc_user2 = get_user_rank_with_count(self.user2.id, "PC")
        self.assertEqual(rank_pc_user1, 1)
        self.assertEqual(rank_pc_user2, 2)

        rank_mob_user1 = get_user_rank_with_count(self.user1.id, "Mobile")
        rank_mob_user2 = get_user_rank_with_count(self.user2.id, "Mobile")
        self.assertEqual(rank_mob_user2, 1)
        self.assertEqual(rank_mob_user1, 2)

    def test_get_level_rank(self):
        rank1 = get_level_rank(self.level1, "PC")
        self.assertEqual(rank1, 1)

        # Level 2 has no PC completions, only Mobile
        rank2 = get_level_rank(self.level2, "PC")
        self.assertIsNone(rank2)

        # Level 2 has Mobile completion
        rank2_mob = get_level_rank(self.level2, "Mobile")
        self.assertEqual(rank2_mob, 1)


class ServiceTests(TestCase):
    def setUp(self):
        self.level_hard = Level.objects.create(place=1, name="Hard Level")
        self.level_easy = Level.objects.create(place=10, name="Easy Level")
        self.user = User.objects.create(username="TestPlayer")

    def test_update_user_hardest(self):
        Victor.objects.create(username=self.user, level=self.level_hard, progress=100, device="PC")
        Victor.objects.create(username=self.user, level=self.level_easy, progress=100, device="PC")
        Victor.objects.create(username=self.user, level=self.level_easy, progress=100, device="Mobile")

        update_user_hardest(self.user)

        self.assertEqual(self.user.hardest_pc, self.level_hard)
        self.assertEqual(self.user.hardest_mobile, self.level_easy)

    def test_get_unique_level_victors(self):
        v1 = Victor.objects.create(username=self.user, level=self.level_hard, progress=100, device="PC")
        Victor.objects.create(username=self.user, level=self.level_hard, progress=50, device="PC")

        qs = Victor.objects.all().order_by('-progress')
        unique = get_unique_level_victors(qs)

        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0], v1)


class ViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

        site = Site.objects.get_current()
        self.app = SocialApp.objects.create(provider='discord', name='Discord', client_id='123')
        self.app.sites.add(site)

        self.level = Level.objects.create(level_id=101, place=1, name="Zodiac", completion_points_pc=1000)
        self.user = User.objects.create(username="Tech", region="RU", score_pc=1000)
        self.auth_user = AuthUser.objects.create_user(username="testauth", password="password")
        DiscordLink.objects.create(auth_user=self.auth_user, gd_user=self.user)

        Victor.objects.create(username=self.user, level=self.level, progress=100, device="PC")

    def test_level_list_api(self):
        response = self.client.get(reverse('level-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json())

    def test_level_detail_api(self):
        response = self.client.get(reverse('level-detail', args=[self.level.level_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], "Zodiac")

    def test_leaderboard_api(self):
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_user_profile_api(self):
        response = self.client.get(reverse('user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], "Tech")

    def test_submit_record_api_unauthenticated(self):
        response = self.client.post(reverse('record-request-list'), {})
        self.assertEqual(response.status_code, 403)

    def test_api_level_by_gd_id(self):
        response = self.client.get(reverse('api-level-by-gd-id', args=[self.level.level_id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['name'], "Zodiac")