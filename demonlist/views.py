import json
from django.db.models import Count, Q
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from allauth.socialaccount.models import SocialAccount

from .models import Level, User, Victor, DiscordLink, RecordRequest
from .selectors import get_user_rank_with_count, get_level_rank
from .services import (
    calculate_user_scores,
    update_user_hardest,
    notify_record_status,
)

# --- Legacy API Functions (Used by Bot) ---


def api_level_by_gd_id(request, level_id):
    cache_key = f"api_level_{level_id}"
    cached_response = cache.get(cache_key)

    if cached_response is None:
        try:
            level = Level.objects.get(level_id=level_id)
            device_filter = "PC"  # Default

            list_rank = get_level_rank(level, device_filter)

            cached_response = {
                "success": True,
                "level_id": level.level_id,
                "name": level.name,
                "place": list_rank,
                "real_db_place": level.place,
            }
            cache.set(cache_key, cached_response, 60 * 15)
        except Level.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Level not found"}, status=404
            )

    return JsonResponse(cached_response)


def api_rank_player_by_discord_id(request, discord_id):
    try:
        social_acc = SocialAccount.objects.get(uid=str(discord_id), provider="discord")
        site_user = social_acc.user
        link = DiscordLink.objects.get(auth_user=site_user)
        gd_player = link.gd_user

        player_id = gd_player.id
        rank_pc = get_user_rank_with_count(player_id, "PC")
        rank_mobile = get_user_rank_with_count(player_id, "Mobile")

        return JsonResponse(
            {
                "success": True,
                "username": gd_player.username,
                "score_pc": float(gd_player.score_pc),
                "score_mobile": float(gd_player.score_mobile),
                "rank_pc": rank_pc,
                "rank_mobile": rank_mobile,
                "hardest_pc": (
                    gd_player.hardest_pc.name if gd_player.hardest_pc else "—"
                ),
                "hardest_mobile": (
                    gd_player.hardest_mobile.name if gd_player.hardest_mobile else "—"
                ),
            }
        )
    except (SocialAccount.DoesNotExist, DiscordLink.DoesNotExist):
        return JsonResponse(
            {"success": False, "error": "Игрок не привязан"}, status=404
        )


def api_profile_player_by_discord_id(request, discord_id):
    try:
        social_acc = SocialAccount.objects.get(uid=str(discord_id), provider="discord")
        site_user = social_acc.user
        link = DiscordLink.objects.get(auth_user=site_user)
        gd_player = link.gd_user

        player_id = gd_player.id
        rank_pc = get_user_rank_with_count(player_id, "PC")
        rank_mobile = get_user_rank_with_count(player_id, "Mobile")

        # Get top 3 achievements (victors)
        top_victors = (
            Victor.objects.filter(username=gd_player, progress=100)
            .select_related("level")
            .order_by("level__place")[:3]
        )
        achievements = [f"{v.level.name} (#{v.level.place})" for v in top_victors]

        victors_count = Victor.objects.filter(username=gd_player, progress=100).count()

        return JsonResponse(
            {
                "success": True,
                "username": gd_player.username,
                "region": gd_player.get_region_display() or "Не указан",
                "score_pc": float(gd_player.score_pc),
                "score_mobile": float(gd_player.score_mobile),
                "rank_pc": rank_pc,
                "rank_mobile": rank_mobile,
                "hardest_pc": (
                    gd_player.hardest_pc.name if gd_player.hardest_pc else "—"
                ),
                "hardest_mobile": (
                    gd_player.hardest_mobile.name if gd_player.hardest_mobile else "—"
                ),
                "victors_count": victors_count,
                "top_achievements": achievements,
                "site_url": f"https://dvsleerstvo.ru/user/{gd_player.id}",
            }
        )
    except (SocialAccount.DoesNotExist, DiscordLink.DoesNotExist):
        return JsonResponse(
            {"success": False, "error": "Игрок не привязан"}, status=404
        )


@csrf_exempt
def api_moderate_record(request, record_id):
    BOT_API_SECRET = getattr(settings, "BOT_API_SECRET")
    if request.method != "POST":
        return JsonResponse({"error": "Метод не разрешен"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный JSON"}, status=400)

    if data.get("secret") != BOT_API_SECRET:
        return JsonResponse({"error": "Доступ запрещен"}, status=403)

    action = data.get("action")
    notes = data.get("notes", "").strip()

    try:
        record = RecordRequest.objects.get(id=record_id)
    except RecordRequest.DoesNotExist:
        return JsonResponse({"error": "Заявка не найдена"}, status=404)

    if record.status != "pending":
        return JsonResponse({"error": "Заявка уже была обработана"}, status=400)

    record.status = action
    record.notes = notes
    record.save()

    if action == "approved":
        Victor.objects.update_or_create(
            username=record.user,
            level=record.level,
            device=record.device,
            defaults={"progress": record.progress, "youtube": record.video},
        )
        update_user_hardest(record.user)
        calculate_user_scores(record.user)

    # Уведомление в ЛС Discord
    notify_record_status(record, action, notes)

    return JsonResponse({"success": True, "action": action})


def api_user_regional_stats(request, gd_account_id):
    try:
        user = User.objects.get(gd_account_id=gd_account_id)
        
        # Calculate ranks
        rank_pc = 0
        if user.score_pc > 0:
            rank_pc = User.objects.filter(score_pc__gt=user.score_pc).count() + 1
            
        rank_mobile = 0
        if user.score_mobile > 0:
            rank_mobile = User.objects.filter(score_mobile__gt=user.score_mobile).count() + 1

        return JsonResponse(
            {
                "success": True,
                "region": user.get_region_display(),
                "region_code": user.region,
                "score_pc": float(user.score_pc),
                "score_mobile": float(user.score_mobile),
                "rank_pc": rank_pc,
                "rank_mobile": rank_mobile,
            }
        )
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"})



@csrf_exempt
def api_update_status(request, gd_account_id):
    # Stub for updating online status via bot
    return JsonResponse({"success": True})


def api_online_players(request):
    players = User.objects.all()
    online_players = [p for p in players if p.is_online]
    data = [
        {
            "username": p.username,
            "activity": p.current_activity,
            "region_code": p.region,
            "rank": 0, # Placeholder if needed
            "score": float(p.score_pc),
            "gd_account_id": p.gd_account_id,
            "is_online": True,
            "last_active": p.last_active.strftime("%Y-%m-%d %H:%M") if p.last_active else "Never"
        } for p in online_players
    ]
    return JsonResponse({"success": True, "players": data})


def api_levels_list(request):
    cache_key = "api_levels_pc_list"
    levels_data = cache.get(cache_key)

    if not levels_data:
        levels = (
            Level.objects.annotate(
                victor_count=Count(
                    "victor", filter=Q(victor__device="PC", victor__progress=100)
                )
            )
            .filter(victor_count__gt=0)
            .order_by("place")
        )

        levels_data = []
        for lvl in levels:
            levels_data.append(
                {
                    "id": lvl.id,
                    "ingame_id": lvl.level_id if lvl.level_id else 0,
                    "name": lvl.name,
                    "placement": get_level_rank(lvl, "PC"),
                    "place": lvl.place,
                    "length": 0,
                }
            )

        cache.set(cache_key, levels_data, 60 * 40)

    return JsonResponse({"data": {"levels": levels_data}})
