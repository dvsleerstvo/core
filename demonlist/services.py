from .api_client import (
    fetch_api_level_list,
    get_player_records_from_api,
    get_player_id,
    get_level_info,
)
from .models import Level, User, Victor
from .selectors import get_levels_rank_with_count, get_level_rank

from django.db.models import When, Case, F, Sum, FloatField
from django.conf import settings

import requests


def get_embed_url(video_url):
    if not video_url:
        return ""

    if video_url.startswith("https://youtu.be/"):
        return video_url.replace("https://youtu.be/", "https://www.youtube.com/embed/")
    if "watch?v=" in video_url:
        video_id = video_url.rsplit("watch?v=", maxsplit=1)[-1]
        if "&" in video_id:
            video_id = video_id.split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    return video_url


def update_user_hardest(user):
    """Обновляет hardest-уровень пользователя."""
    hardest_pc = (
        Victor.objects.filter(username=user, progress=100, device="PC")
        .select_related("level")
        .order_by("level__place")
        .first()
    )
    hardest_mobile = (
        Victor.objects.filter(username=user, progress=100, device="Mobile")
        .select_related("level")
        .order_by("level__place")
        .first()
    )

    user.hardest_pc = hardest_pc.level if hardest_pc else None
    user.hardest_mobile = hardest_mobile.level if hardest_mobile else None
    user.save()


def add_victors(usernames_to_process):
    error = set()
    for username in usernames_to_process:
        user_data = get_player_id(username)
        demonlist_id = user_data["id"]
        user_records = get_player_records_from_api(demonlist_id)

        if user_records is None:
            print(f"Пользователь '{username}' не найден в данных API." f" Пропускаем.")
            continue

        badge = user_data["badge"]
        badge_mapped = get_badge(badge)

        player_obj = get_user_objects(username, user_data['id'])
        for item in user_records:
            save_records_to_db(item, badge_mapped, player_obj)

        calculate_user_scores(player_obj)

        update_user_hardest(player_obj)

    print(f"Не получилось добавить {error}")
    return {
        "status": "success",
        "processed": len(usernames_to_process),
        "errors": list(error),
    }


def check_change(data, api_lookup, level, device_type):
    updated_levels = []
    api_level = api_lookup.get(level.level_id)

    if not api_level:
        print(f"API data for {level.name} not found.")
        return updated_levels

    place = api_level["placement"]
    rank = get_level_rank(level, device_type)
    completion_points, list_points, list_percentage = calculate_score(
        rank, api_level["ingame_id"], data
    )

    suffix = get_suffix(device_type)

    if suffix:
        setattr(level, "completion_points" + suffix, completion_points)
        setattr(level, "list_points" + suffix, list_points)
        setattr(level, "list_percentage" + suffix, list_percentage)
        level.place = place
        updated_levels.append(level)

    return updated_levels


def get_unique_level_victors(queryset):
    """Оставляет только уникальные уровни в QuerySet."""
    unique_victors = []
    seen_levels = set()
    for victor in queryset:
        if victor.level_id not in seen_levels:
            unique_victors.append(victor)
            seen_levels.add(victor.level_id)
    return unique_victors


def average_of_six_placements(placements: list):
    if not isinstance(placements, list):
        raise TypeError("Тип аргумента функции должна быть строка")

    summary = 0

    if len(placements) < 6:
        min_placement = Level.objects.order_by("place").first()
        while len(placements) < 6:
            placements.append(min_placement)

    for placement in placements:
        if placement < 0:
            raise ValueError("Значение place не может быть отрицательным")
        summary += placement

    average = summary / 6

    return average


def update_levels_from_api(device_type):
    """Обновляет completion_points, list_points
    и list_percentage у уровней, у которых есть Victor."""
    data = fetch_api_level_list()

    api_lookup = {item["ingame_id"]: item for item in data}
    levels = get_levels_rank_with_count(device_type)
    for i, level in enumerate(levels):
        level.list_rank = i + 1

    for level in levels:
        suffix = get_suffix(device_type)
        updated_levels = check_change(data, api_lookup, level, device_type)
        Level.objects.bulk_update(
            updated_levels,
            [
                f"completion_points{suffix}",
                f"list_points{suffix}",
                f"list_percentage{suffix}",
                "place",
            ],
        )


def update_user_data(sender, user, **kwargs):
    """Обновляет очки и hardest пользователя при изменении Victor."""
    calculate_user_scores(user)
    update_user_hardest(user)


def find_level_data(level_id, api_data):
    for level in api_data:
        if level["ingame_id"] == level_id:
            return level
    return None


def update_info_from_api(sender, instance, **kwargs):
    api_data = fetch_api_level_list()
    if not api_data:
        return

    level = find_level_data(instance.level_id, api_data)
    if not level:
        return

    level_data = get_level_info(level["placement"])
    level_data = level_data.json().get("data", [])
    if not isinstance(level_data, dict):
        return

    updated_fields = {}
    verification = level_data.get("verification") or {}

    if instance.place != level_data.get("placement"):
        updated_fields["place"] = level_data.get("placement")
    
    new_description = level_data.get("description") or ''
    if instance.description != new_description:
        updated_fields["description"] = new_description
        
    new_verifier = verification.get("username") or ''
    if instance.verifier != new_verifier:
        updated_fields["verifier"] = new_verifier
        
    if instance.level_id != level_data.get("ingame_id"):
        updated_fields["level_id"] = level_data.get("ingame_id")
        
    new_video = verification.get("video_url") or ''
    if instance.video != new_video:
        updated_fields["video"] = new_video
        
    new_published = level_data.get("holder") or ''
    if instance.published != new_published:
        updated_fields["published"] = new_published
        
    new_creator = level_data.get("creator") or ''
    if instance.creator != new_creator:
        updated_fields["creator"] = new_creator

    # Use global_id (data['id']) if available for consistency with import-levels, 
    # but the failing row showed ingame_id was being used here.
    # To avoid breaking existing thumbnails, we'll use data['id'] which is 3030.
    global_id = level_data.get("id")
    if global_id:
        thumbnail_url = f"https://thumbnails.demonlist.org/classic/{global_id}.png"
        if instance.thumbnail_url != thumbnail_url:
            updated_fields["thumbnail_url"] = thumbnail_url

    if updated_fields:
        Level.objects.filter(pk=instance.pk).update(**updated_fields)


def calculate_user_scores(user):
    """Обновляет очки пользователя по PC и Mobile."""

    for device_type, field_name, suffix in [
        ("PC", "score_pc", "pc"),
        ("Mobile", "score_mobile", "mobile"),
    ]:
        victors = Victor.objects.filter(username=user, device=device_type).annotate(
            completion_points=F(f"level__completion_points_{suffix}"),
            list_points=F(f"level__list_points_{suffix}"),
            list_percentage=F(f"level__list_percentage_{suffix}"),
        )

        result = victors.aggregate(
            total=Sum(
                Case(
                    When(progress=100, then=F("completion_points")),
                    When(progress__gte=F("list_percentage"), then=F("list_points")),
                    default=0,
                    output_field=FloatField(),
                )
            )
        )

        setattr(user, field_name, result["total"] or 0)

    user.save()


def get_suffix(device_type):
    suffix = (
        "_pc" if device_type == "PC" else "_mobile" if device_type == "Mobile" else None
    )
    return suffix


def save_records_to_db(level, badge, player_obj):
    try:
        level_name_obj = Level.objects.get(global_demonlist_id=level["id"])
    except Level.DoesNotExist:
        print(f"Уровень с ID {level['id']} не найден в локальной БД. Пропуск.")
        return

    video_url = level.get("video_url")
    percentage = level.get("percent", 100)

    if not Victor.objects.filter(username=player_obj, level=level_name_obj).exists():
        victor = Victor(
            username=player_obj,
            level=level_name_obj,
            youtube=video_url,
            progress=percentage,
            device=badge,
        )
        victor.save()
        print(f"Добавлен победитель: {player_obj.username} - {level_name_obj.name}")
    else:
        print(
            f"Победитель уже существует: {player_obj.username} - {level_name_obj.name}"
        )


def get_badge(badge):
    if badge == "pc":
        badge_mapped = "PC"
    elif badge == "mobile":
        badge_mapped = "Mobile"
    else:
        badge_mapped = None
    return badge_mapped


def calculate_score(place: int, level_id: str, api_data):
    level_data = find_level_data(level_id, api_data)
    list_percentage = (
        level_data["list_percent"] if int(level_data["placement"]) <= 150 else 0
    )

    if place < 1:
        point_completion = 0
    elif place <= 8:
        point_completion = 1000 - (place - 1) * 40
    elif place == 9:
        point_completion = 680
    elif place == 10:
        point_completion = 620
    elif place <= 20:
        point_completion = 600 - (place - 11) * 20
    elif place <= 50:
        point_completion = 416 - (place - 21) * 4
    elif place <= 149:
        point_completion = round(292 - (place - 51) * 2.85, 2)
    elif place <= 299:
        point_completion = round(10 - (place - 150) * 0.06, 2)
    else:
        point_completion = 1

    point_list = (
        round(point_completion / 4, 2)
        if 1 <= place <= 150 and list_percentage != 0
        else 0
    )

    return point_completion, point_list, list_percentage


def send_discord_webhook(message):
    webhook_url = getattr(settings, "DISCORD_WEBHOOK_URL", "ВАШ_URL_ВЕБХУКА_ЗДЕСЬ")

    if not webhook_url:
        return

    data = {"content": message}

    try:
        requests.post(webhook_url, json=data, timeout=5)
    except Exception as e:
        print(f"Ошибка при отправке webhook в Discord: {e}")


def send_discord_dm(discord_id, content):
    BOT_TOKEN = getattr(settings, "BOT_TOKEN")
    if not BOT_TOKEN:
        print("CRITICAL: BOT_TOKEN not found in settings!")
        return

    headers = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}
    try:
        # 1. Создаем DM канал
        dm_res = requests.post(
            "https://discord.com/api/v10/users/@me/channels",
            headers=headers,
            json={"recipient_id": str(discord_id)},
            timeout=5
        )

        if dm_res.status_code == 200:
            channel_id = dm_res.json().get("id")
            # 2. Отправляем сообщение
            msg_res = requests.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers=headers,
                json={"content": content},
                timeout=5
            )
            if msg_res.status_code != 200:
                print(f"Failed to send message: {msg_res.status_code} - {msg_res.text}")
        else:
            print(f"Failed to create DM channel: {dm_res.status_code} - {dm_res.text}")
    except Exception as e:
        print(f"Error sending Discord DM: {e}")


def notify_record_status(record, action, notes=None):
    """Отправляет уведомление игроку в ЛС Discord о статусе рекорда."""
    try:
        from .models import DiscordLink
        from allauth.socialaccount.models import SocialAccount

        link = DiscordLink.objects.filter(gd_user=record.user).first()
        if not link:
            print(f"Notification skipped: No DiscordLink for user {record.user}")
            return
        
        if not link.notifications_enabled:
            print(f"Notification skipped: DMs disabled for user {record.user}")
            return

        social_acc = SocialAccount.objects.filter(
            user=link.auth_user, provider="discord"
        ).first()
        if not social_acc:
            print(f"Notification skipped: No SocialAccount (discord) for user {record.user}")
            return

        discord_id = social_acc.uid
        status_ru = "ОДОБРЕН" if action == "approved" else "ОТКЛОНЕН"
        
        msg = f"🔔 Ваш рекорд на уровень **{record.level.name}** был **{status_ru}** модератором.\n"
        if notes:
            msg += f"📝 Заметка: *{notes}*"

        print(f"Attempting to send DM to discord_id: {discord_id}")
        send_discord_dm(discord_id, msg)
    except Exception as e:
        print(f"Failed to send DM notification: {e}")


def send_record_moderation_message(content, record_id):
    BOT_TOKEN = getattr(settings, "BOT_TOKEN")
    CHANNEL_ID = getattr(settings, "REQUEST_CHANNEL_ID")

    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"

    headers = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}

    payload = {
        "content": content,
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "label": "✅ Принять",
                        "style": 3,
                        "custom_id": f"approve_{record_id}",
                    },
                    {
                        "type": 2,
                        "label": "❌ Отклонить",
                        "style": 4,
                        "custom_id": f"reject_{record_id}",
                    },
                    {
                        "type": 2,
                        "label": "📝 Заметка",
                        "style": 2,
                        "custom_id": f"note_{record_id}",
                    },
                ],
            }
        ],
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 200


def get_user_objects(username, demonlist_id):
    player_obj, created = User.objects.get_or_create(
        username=username, defaults={"global_demonlist_user_id": demonlist_id}
    )
    if created:
        send_discord_webhook(f"👤 Добавлен новый игрок: **{username}**!")

    return player_obj


def update_places(levels):
    response = fetch_api_level_list()

    for level in levels:
        for api in response:
            if level.level_id == api["ingame_id"]:
                if level.place != api["placement"]:
                    level.place = api["placement"]
                    level.save()


def get_all_levels():
    levels = Level.objects.all()
    return levels
