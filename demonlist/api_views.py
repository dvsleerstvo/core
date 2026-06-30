from django.db.models import Count, Q, Sum, F
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .variable import STATE_CHOICES
from .models import Level, User, Victor, RecordRequest
from .serializers import (
    LevelSerializer,
    UserSerializer,
    VictorSerializer,
    RecordRequestSerializer,
)
from .services import notify_record_status, send_record_moderation_message
from .selectors import get_level_rank, get_user_rank_with_count
from .utils import get_device_filter


class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Level.objects.all().order_by("place")
    serializer_class = LevelSerializer
    lookup_field = "level_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        device_filter = get_device_filter(self.request)

        queryset = (
            queryset.annotate(
                victor_count=Count(
                    "victor",
                    filter=Q(victor__device=device_filter, victor__progress=100),
                )
            )
            .filter(victor_count__gt=0)
            .order_by("place")
        )

        search_query = self.request.query_params.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def all_for_submit(self, request):
        levels = Level.objects.all().order_by("place")
        data = [
            {"id": level.id, "name": level.name, "place": level.place, "creator": level.creator}
            for level in levels
        ]
        return Response(data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Get all passed IDs once for the user (not paginated)
        passed_ids = []
        if request.user.is_authenticated and hasattr(request.user, "discord_link"):
            gd_user = request.user.discord_link.gd_user
            device_filter = get_device_filter(request)
            passed_ids = list(
                Victor.objects.filter(
                    username=gd_user, device=device_filter, progress=100
                ).values_list("level_id", flat=True)
            )

        # Pre-calculate global ranks to ensure search doesn't reset them
        device_filter = get_device_filter(request)
        
        # Get all levels that would be in the full leaderboard
        full_leaderboard = Level.objects.annotate(
            victor_count=Count(
                "victor",
                filter=Q(victor__device=device_filter, victor__progress=100),
            )
        ).filter(victor_count__gt=0).order_by("place").values_list("id", flat=True)
        
        # Create a mapping of level_id -> global_rank
        rank_map = {level_id: index + 1 for index, level_id in enumerate(full_leaderboard)}

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            for item in data:
                item["list_rank"] = rank_map.get(item["id"])
                item["is_passed"] = item["id"] in passed_ids
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        for item in data:
            item["list_rank"] = rank_map.get(item["id"])
            item["is_passed"] = item["id"] in passed_ids
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        device_filter = get_device_filter(request)

        serializer = self.get_serializer(instance)
        data = serializer.data
        data["rank"] = get_level_rank(instance, device_filter)

        # Sort: First victor first, then by progress descending
        victors = Victor.objects.filter(level=instance, device=device_filter).order_by(
            "-is_first_victor", "-progress", "created_at"
        )
        data["victors"] = VictorSerializer(victors, many=True).data

        # Priority for video:
        first_victor_marked = (
            victors.filter(is_first_victor=True, youtube__isnull=False)
            .exclude(youtube="")
            .first()
        )
        if first_victor_marked:
            data["display_video_url"] = first_victor_marked.embed_url
        else:
            first_chronological = (
                victors.filter(progress=100, youtube__isnull=False)
                .exclude(youtube="")
                .order_by("created_at")
                .first()
            )
            data["display_video_url"] = (
                first_chronological.embed_url
                if first_chronological
                else instance.embed_url
            )

        return Response(data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = None  # Disable pagination for this view

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def by_gd_id(self, request):
        gd_id = request.query_params.get("id")
        if not gd_id:
            return Response({"error": "No ID provided"}, status=400)

        try:
            user = User.objects.get(gd_account_id=gd_id)
            return Response(
                {
                    "username": user.username,
                    "region": user.region,
                    "rank_pc": get_user_rank_with_count(user.id, "PC"),
                    "rank_mobile": get_user_rank_with_count(user.id, "Mobile"),
                    "score_pc": float(user.score_pc),
                    "score_mobile": float(user.score_mobile),
                }
            )
        except User.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

    def get_queryset(self):
        queryset = super().get_queryset()
        device_filter = get_device_filter(self.request)
        device_field = "score_mobile" if device_filter == "Mobile" else "score_pc"

        sort_by = self.request.query_params.get("sort", "score")
        order = self.request.query_params.get("order", "desc")

        if sort_by == "score":
            order_field = f"-{device_field}" if order == "desc" else device_field
        elif sort_by == "username":
            order_field = "-username" if order == "desc" else "username"
        elif sort_by == "hardest":
            hardest_field = f"hardest_{device_filter.lower()}__place"
            order_field = hardest_field if order == "asc" else f"-{hardest_field}"
        else:
            order_field = f"-{device_field}"

        # We DO NOT filter by score > 0 here to allow retrieve() for any user
        queryset = queryset.select_related("hardest_pc", "hardest_mobile").order_by(
            order_field
        )

        search_query = self.request.query_params.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(username__icontains=search_query)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Apply score filtering ONLY for the list (leaderboard)
        device_filter = get_device_filter(request)
        device_field = "score_mobile" if device_filter == "Mobile" else "score_pc"
        queryset = queryset.filter(**{f"{device_field}__gt": 0})

        # Pre-calculate global ranks to ensure search doesn't reset them
        # Note: Leaderboard rank is always based on score descending
        full_leaderboard = User.objects.filter(**{f"{device_field}__gt": 0}).order_by(f"-{device_field}", "id").values_list("id", flat=True)
        rank_map = {user_id: index + 1 for index, user_id in enumerate(full_leaderboard)}

        # Get IDs of levels passed by current user
        passed_ids = []
        if request.user.is_authenticated and hasattr(request.user, "discord_link"):
            gd_user = request.user.discord_link.gd_user
            device_filter = get_device_filter(request)
            passed_ids = Victor.objects.filter(
                username=gd_user, device=device_filter, progress=100
            ).values_list("level_id", flat=True)

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        # Inject rank and is_passed flag
        for item in data:
            item["rank"] = rank_map.get(item["id"])
            item["is_passed"] = item["id"] in passed_ids

        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        data["rank_pc"] = get_user_rank_with_count(instance.id, "PC")
        data["rank_mobile"] = get_user_rank_with_count(instance.id, "Mobile")

        victors = (
            Victor.objects.filter(username=instance)
            .select_related("level")
            .order_by("level__place")
        )

        data["victors_on_pc"] = VictorSerializer(
            victors.filter(device="PC", progress=100), many=True
        ).data
        data["victors_on_mobile"] = VictorSerializer(
            victors.filter(device="Mobile", progress=100), many=True
        ).data
        data["progress_on_pc"] = VictorSerializer(
            victors.filter(device="PC", progress__lt=100), many=True
        ).data
        data["progress_on_mobile"] = VictorSerializer(
            victors.filter(device="Mobile", progress__lt=100), many=True
        ).data

        # Only include record requests if the user is viewing their own profile
        if request.user.is_authenticated and hasattr(request.user, "discord_link"):
            user_gd_id = request.user.discord_link.gd_user.id
            if user_gd_id == instance.id:
                requests = (
                    RecordRequest.objects.filter(user=instance)
                    .select_related("level")
                    .order_by("-created_at")
                )
                data["record_requests"] = RecordRequestSerializer(
                    requests, many=True
                ).data
            else:
                data["record_requests"] = None
        else:
            data["record_requests"] = None

        return Response(data)


class RegionalLeaderboardView(APIView):
    def get(self, request):
        device_type = get_device_filter(request)
        score_field = f"score_{device_type.lower()}"

        state_dict = dict(STATE_CHOICES)
        
        from django.db.models import OuterRef, Subquery

        # Subquery to find the level ID of the hardest completion (place > 0)
        hardest_level_id_subquery = Victor.objects.filter(
            username__region=OuterRef('region'),
            progress=100,
            device=device_type,
            level__place__gt=0
        ).order_by('level__place').values('level_id')[:1]

        # Subquery to find the place of that hardest completion
        hardest_level_place_subquery = Victor.objects.filter(
            username__region=OuterRef('region'),
            progress=100,
            device=device_type,
            level__place__gt=0
        ).order_by('level__place').values('level__place')[:1]

        # 1. Get regions with their scores and hardest level info
        regions_qs = (
            User.objects.filter(**{f"{score_field}__gt": 0})
            .exclude(Q(region__isnull=True) | Q(region=""))
            .values("region")
            .annotate(
                total_score=Sum(score_field),
                hardest_level_id=Subquery(hardest_level_id_subquery),
                best_place=Subquery(hardest_level_place_subquery)
            )
        )

        # 2. Map level IDs to names
        level_ids = [r["hardest_level_id"] for r in regions_qs if r["hardest_level_id"]]
        levels_map = {lvl.id: lvl.name for lvl in Level.objects.filter(id__in=level_ids)}

        regions_list = []
        for r in regions_qs:
            region_code = r["region"]
            full_name = state_dict.get(region_code, region_code)
            regions_list.append(
                {
                    "region_code": region_code,
                    "region_name": full_name,
                    "total_score": r["total_score"],
                    "best_place": r["best_place"] or 999999,
                    "hardest_name": levels_map.get(r["hardest_level_id"], "—"),
                }
            )

        # Sort by score descending to assign global ranks
        regions_list.sort(key=lambda x: x["total_score"], reverse=True)
        for index, item in enumerate(regions_list):
            item["rank"] = index + 1

        sort_by = request.query_params.get("sort", "score")
        order = request.query_params.get("order", "desc")
        search_query = request.query_params.get("q", "").strip().lower()

        if search_query:
            regions_list = [
                r
                for r in regions_list
                if search_query in r["region_name"].lower()
                or search_query in r["region_code"].lower()
            ]

        if sort_by == "hardest":
            regions_list.sort(key=lambda x: x["best_place"], reverse=(order == "asc"))
        elif sort_by == "score":
            regions_list.sort(key=lambda x: x["total_score"], reverse=(order == "desc"))

        return Response(regions_list)


class RegionProfileView(APIView):
    def get(self, request, region_code):
        state_dict = dict(STATE_CHOICES)
        region_name = state_dict.get(region_code, region_code)

        def get_region_rank(field):
            all_regions = (
                User.objects.exclude(Q(region__isnull=True) | Q(region=""))
                .values("region")
                .annotate(total=Sum(field))
                .order_by("-total")
            )
            for i, r in enumerate(all_regions):
                if r["region"] == region_code:
                    return i + 1
            return None

        users = User.objects.filter(region=region_code)
        score_pc = users.aggregate(Sum("score_pc"))["score_pc__sum"] or 0
        score_mobile = users.aggregate(Sum("score_mobile"))["score_mobile__sum"] or 0

        # Victors and progress (De-duplicated by level)
        all_victors = (
            Victor.objects.filter(username__region=region_code)
            .select_related("level", "username")
            .order_by("level__place", "-is_first_victor", "created_at")
        )

        def get_unique_records(qs):
            unique_map = {}
            for rec in qs:
                if rec.level_id not in unique_map:
                    unique_map[rec.level_id] = rec
            return list(unique_map.values())

        victors_pc = get_unique_records(all_victors.filter(device="PC", progress=100))
        victors_mobile = get_unique_records(
            all_victors.filter(device="Mobile", progress=100)
        )
        progress_pc = get_unique_records(
            all_victors.filter(device="PC", progress__lt=100)
        )
        progress_mobile = get_unique_records(
            all_victors.filter(device="Mobile", progress__lt=100)
        )

        players = users.annotate(
            total_score=F("score_pc") + F("score_mobile")
        ).order_by("-total_score")

        players_data = []
        for i, p in enumerate(players):
            players_data.append(
                {
                    "id": p.id,
                    "username": p.username,
                    "score_pc": p.score_pc,
                    "score_mobile": p.score_mobile,
                    "total_score": p.total_score,
                    "region_rank": i + 1,
                }
            )

        return Response(
            {
                "region_name": region_name,
                "region_code": region_code,
                "score_pc": score_pc,
                "score_mobile": score_mobile,
                "rank_pc": get_region_rank("score_pc"),
                "rank_mobile": get_region_rank("score_mobile"),
                "victors_on_pc": VictorSerializer(victors_pc, many=True).data,
                "victors_on_mobile": VictorSerializer(victors_mobile, many=True).data,
                "progress_on_pc": VictorSerializer(progress_pc, many=True).data,
                "progress_on_mobile": VictorSerializer(progress_mobile, many=True).data,
                "players": players_data,
            }
        )


class AuthMeView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"authenticated": False}, status=status.HTTP_200_OK)

        user = request.user
        data = {
            "authenticated": True,
            "username": user.username,
            "id": user.id,
        }

        if hasattr(user, "discord_link"):
            data["gd_user_id"] = user.discord_link.gd_user.id
            data["gd_username"] = user.discord_link.gd_user.username
            data["notifications_enabled"] = user.discord_link.notifications_enabled

        return Response(data)


class UpdateSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "discord_link"):
            return Response(
                {"error": "No discord link found"}, status=status.HTTP_400_BAD_REQUEST
            )

        enabled = request.data.get("notifications_enabled", True)
        link = request.user.discord_link
        link.notifications_enabled = enabled
        link.save()
        return Response(
            {"success": True, "notifications_enabled": link.notifications_enabled}
        )


class LogoutView(APIView):
    def post(self, request):
        from django.contrib.auth import logout

        logout(request)
        return Response({"success": True})

    def get(self, request):
        from django.contrib.auth import logout
        from django.shortcuts import redirect
        from django.conf import settings

        logout(request)
        return redirect(getattr(settings, "LOGOUT_REDIRECT_URL", "/"))


class RecordRequestViewSet(viewsets.ModelViewSet):
    queryset = RecordRequest.objects.all()
    serializer_class = RecordRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def moderate(self, request, pk=None):
        instance = self.get_object()
        action_type = request.data.get("action")  # 'approve' or 'reject'
        notes = request.data.get("notes", "").strip()

        if action_type == "approve":
            instance.status = "approved"
            instance.notes = notes
            instance.save()

            # Create Victor record
            Victor.objects.update_or_create(
                username=instance.user,
                level=instance.level,
                device=instance.device,
                defaults={"progress": instance.progress, "youtube": instance.video},
            )

            # Уведомление в ЛС
            notify_record_status(instance, "approved", notes)

            return Response({"status": "approved"})

        elif action_type == "reject":
            instance.status = "rejected"
            instance.notes = notes
            instance.save()

            # Уведомление в ЛС
            notify_record_status(instance, "rejected", notes)

            return Response({"status": "rejected"})

        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        if not hasattr(request.user, "discord_link"):
            return Response(
                {"error": "Account not linked to a GD profile"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        gd_user = request.user.discord_link.gd_user

        # Inject user ID into the data before passing to serializer
        data = request.data.copy()
        data["user"] = gd_user.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        level = serializer.validated_data["level"]
        progress = serializer.validated_data["progress"]
        device = serializer.validated_data["device"]

        list_percentage = (
            level.list_percentage_pc if device == "PC" else level.list_percentage_mobile
        )
        if progress < list_percentage:
            return Response(
                {"error": f"Progress below minimum ({list_percentage}%)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Victor.objects.filter(
            username=gd_user, level=level, device=device, progress__gte=progress
        ).exists():
            return Response(
                {"error": "Higher or equal record already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if RecordRequest.objects.filter(
            user=gd_user,
            level=level,
            device=device,
            progress__gte=progress,
            status__in=["pending", "approved"],
        ).exists():
            return Response(
                {"error": "Request already pending or approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = serializer.save()

        try:
            content = f"Новая заявка на рекорд!\nИгрок: **{gd_user}**\nУровень: **{level}** ({level.creator})\nГлобал: **{level.place}**\nПрогресс: **{progress}%**\nУстройство: **{device}**\nВидео: {instance.video}"
            send_record_moderation_message(content, instance.id)
        except Exception as e:
            print(f"Error sending Discord message: {e}")

        return Response(serializer.data, status=status.HTTP_201_CREATED)
