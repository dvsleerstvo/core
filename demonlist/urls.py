from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from . import views, api_views

router = DefaultRouter()
router.register(r'levels', api_views.LevelViewSet, basename='level')
router.register(r'users', api_views.UserViewSet, basename='user')
router.register(r'record-requests', api_views.RecordRequestViewSet, basename='record-request')

urlpatterns = [
    # Новое API для Svelte
    path('api/v2/', include(router.urls)),
    path('api/v2/regional-leaderboard/', api_views.RegionalLeaderboardView.as_view(), name='api-regional-leaderboard'),
    path('api/v2/region/<str:region_code>/', api_views.RegionProfileView.as_view(), name='api-region-profile'),
    path('api/v2/auth/me/', api_views.AuthMeView.as_view(), name='api-auth-me'),
    path('api/v2/auth/settings/', api_views.UpdateSettingsView.as_view(), name='api-auth-settings'),
    path('api/v2/auth/logout/', api_views.LogoutView.as_view(), name='api-auth-logout'),
    
    # Старое API (оставляем для бота)
    path('api/level/<int:level_id>/', views.api_level_by_gd_id, name='api-level-by-gd-id'),
    path('api/rank/<str:discord_id>', views.api_rank_player_by_discord_id, name='api-rank-by-discord-id'),
    path('api/profile/<str:discord_id>', views.api_profile_player_by_discord_id, name='api-profile-by-discord-id'),
    path('api/records/<int:record_id>/moderate/', views.api_moderate_record, name='api-moderate-record'),
    path('api/levels/', views.api_levels_list, name='api-levels-list'),
    path('api/user/stats/<int:gd_account_id>/', views.api_user_regional_stats, name='api-user-stats'),
    path('api/user/status/update/<int:gd_account_id>/', views.api_update_status, name='api-update-status'),
    path('api/online_players/', views.api_online_players, name='api-online-players'),
    
    # Системные
    path("favicon.ico", RedirectView.as_view(url="/static/img/favicon.ico")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
