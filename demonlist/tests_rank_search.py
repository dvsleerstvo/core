from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, Level, Victor

class RankSearchTest(APITestCase):
    def setUp(self):
        # Create levels to give players some scores (though we can set scores directly)
        self.level1 = Level.objects.create(name="Top 1", place=1, level_id=1, completion_points_pc=100)
        self.level2 = Level.objects.create(name="Top 2", place=2, level_id=2, completion_points_pc=50)

        self.player1 = User.objects.create(username="Alice", score_pc=100)
        self.player2 = User.objects.create(username="Bob", score_pc=50)
        
    def test_search_keeps_global_rank(self):
        # Without search: Alice is #1, Bob is #2
        response = self.client.get('/api/v2/users/?device=pc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        players = response.data
        self.assertEqual(players[0]['username'], "Alice")
        self.assertEqual(players[0]['rank'], 1)
        self.assertEqual(players[1]['username'], "Bob")
        self.assertEqual(players[1]['rank'], 2)

        # Search for Bob
        response = self.client.get('/api/v2/users/?device=pc&q=Bob')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        players = response.data
        self.assertEqual(len(players), 1)
        self.assertEqual(players[0]['username'], "Bob")
        # THIS IS THE BUG: Currently it returns 1, but should return 2
        self.assertEqual(players[0]['rank'], 2)

class LevelRankSearchTest(APITestCase):
    def setUp(self):
        self.p1 = User.objects.create(username="Alice")
        self.level1 = Level.objects.create(name="Acheron", place=1, level_id=1)
        self.level2 = Level.objects.create(name="Slaughterhouse", place=2, level_id=2)
        
        # Rankings are only for levels with at least one victor
        Victor.objects.create(username=self.p1, level=self.level1, progress=100, device='PC')
        Victor.objects.create(username=self.p1, level=self.level2, progress=100, device='PC')

    def test_level_search_keeps_global_rank(self):
        # Without search
        response = self.client.get('/api/v2/levels/?device=pc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        levels = response.data['results']
        self.assertEqual(levels[0]['name'], "Acheron")
        self.assertEqual(levels[0]['list_rank'], 1)
        self.assertEqual(levels[1]['name'], "Slaughterhouse")
        self.assertEqual(levels[1]['list_rank'], 2)

        # Search for Slaughterhouse
        response = self.client.get('/api/v2/levels/?device=pc&q=Slaughterhouse')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        levels = response.data['results']
        self.assertEqual(len(levels), 1)
        self.assertEqual(levels[0]['name'], "Slaughterhouse")
        # BUG: Currently it returns 1, should be 2
        self.assertEqual(levels[0]['list_rank'], 2)

class RegionalRankSearchTest(APITestCase):
    def setUp(self):
        # Alice is in PK, Bob is in KHK
        # PK total score: 100, KHK total score: 50
        self.p1 = User.objects.create(username="Alice", score_pc=100, region="PK")
        self.p2 = User.objects.create(username="Bob", score_pc=50, region="KHK")

    def test_regional_search_keeps_global_rank(self):
        # Without search: PK is #1, KHK is #2
        response = self.client.get('/api/v2/regional-leaderboard/?device=pc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        regions = response.data
        self.assertEqual(regions[0]['region_code'], "PK")
        self.assertEqual(regions[0]['rank'], 1)
        self.assertEqual(regions[1]['region_code'], "KHK")
        self.assertEqual(regions[1]['rank'], 2)

        # Search for KHK (Хабаровск)
        # Note: RegionalLeaderboardView searches by region_name or code
        response = self.client.get('/api/v2/regional-leaderboard/?device=pc&q=KHK')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        regions = response.data
        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0]['region_code'], "KHK")
        # Should be 2, not 1
        self.assertEqual(regions[0]['rank'], 2)
