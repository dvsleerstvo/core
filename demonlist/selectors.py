from .models import Level, User
from django.db.models import Q, Count


def get_user_rank_with_count(user_id, device):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

    if device == "PC":
        if not user.score_pc or user.score_pc <= 0:
            return None
        return User.objects.filter(score_pc__gt=user.score_pc).count() + 1

    elif device == "Mobile":
        if not user.score_mobile or user.score_mobile <= 0:
            return None
        return User.objects.filter(score_mobile__gt=user.score_mobile).count() + 1

    return None


def get_levels_rank_with_count(device_type):
    levels_with_victors = (
        Level.objects.annotate(
            victor_count=Count(
                "victor",
                filter=Q(victor__device=device_type, victor__progress=100),
            )
        )
        .filter(victor_count__gt=0)
        .order_by("place")
    )

    for i, level in enumerate(levels_with_victors):
        level.list_rank = i + 1

    return levels_with_victors


def get_level_rank(level, device_filter):
    levels_with_victors = get_levels_rank_with_count(device_filter)

    if not levels_with_victors.filter(pk=level.pk).exists():
        return None

    rank = levels_with_victors.filter(place__lt=level.place).count() + 1
    return rank
