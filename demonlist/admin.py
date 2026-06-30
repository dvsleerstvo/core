
from django.contrib import admin, messages
from django.db.models import Count
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import path
from unfold.admin import ModelAdmin

from .models import Level, User, Victor, DiscordLink, RecordRequest
from .services import (
    calculate_user_scores,
    update_levels_from_api,
    add_victors,
    send_discord_webhook,
    notify_record_status,
    update_user_hardest,
    update_places,
)


@admin.action(description="Обновить позиции")
def update_places_admin(modeladmin, request, queryset):
    update_places(queryset)


@admin.action(description="Заменить устройства на ПК")
def update_devicetype_pc(modeladmin, request, queryset):
    for victor in queryset:
        if victor.device != "PC":
            victor.device = "PC"
            victor.save()


@admin.action(description="Заменить устройства на Телефон")
def update_devicetype_mobile(modeladmin, request, queryset):
    for victor in queryset:
        if victor.device != "Mobile":
            victor.device = "Mobile"
            victor.save()


@admin.action(description="Обновить очки игрока")
def update_score_action(modeladmin, request, queryset):
    for user in queryset:
        user.update_score()


@admin.register(Level)
class LevelAdmin(ModelAdmin):
    """Кастомные настройки для отображения уровней в админке"""

    list_display = ("id", "level_id", "name", "place", "has_victors_display")
    search_fields = ["level_id", "name", "place"]
    ordering = ["place"]
    readonly_fields = (
        "level_id",
        "place",
        "creator",
        "description",
        "published",
        "verifier",
        "list_percentage_pc",
        "list_points_pc",
        "completion_points_pc",
        "list_percentage_mobile",
        "list_points_mobile",
        "completion_points_mobile",
    )
    actions = [update_places]
    change_list_template = "admin/level_changelist.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(num_victors=Count("victor")).order_by("-num_victors")

    def has_victors_display(self, obj):
        return obj.num_victors

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "update-scores/",
                self.admin_site.admin_view(self.update_scores_view),
                name="update-scores",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        if not extra_context:
            extra_context = {}
            extra_context["custom_button"] = True
        return super().changelist_view(request, extra_context=extra_context)

    def update_scores_view(self, request):
        update_levels_from_api("PC")
        update_levels_from_api("Mobile")
        return redirect("admin:demonlist_level_changelist")

    has_victors_display.admin_order_field = "num_victors"
    has_victors_display.short_description = "Есть Викторы"


@admin.register(Victor)
class VictorAdmin(ModelAdmin):
    """Кастомные настройки для отображения викторов в админке"""

    list_display = ("username", "level", "youtube", "device", "created_at")
    search_fields = ("username__username", "level__name")
    autocomplete_fields = ["username", "level"]
    readonly_fields = ("created_at",)
    change_list_template = "admin/victor_changelist.html"
    actions = [update_devicetype_pc, update_devicetype_mobile]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("add-victors/<str:username>/", self.admin_site.admin_view(self.add_victors), name="add-victors"),
            path("add-victors-all/", self.admin_site.admin_view(self.add_victors_all), name="add-victors-all"),
        ]
        return custom_urls + urls

    def add_victors(self, request, username):
        username_list = []
        username_list.append(username)
        add_victors(username_list)
        return redirect("admin:demonlist_victor_changelist")

    def add_victors_all(self, request):
        all_local_users = [user_obj.username for user_obj in User.objects.all()]

        result = add_victors(all_local_users)

        if result["status"] == "success":
            message = (
                f"Процесс завершен."
                f" Обработано {result['processed']} пользователей."
                f" Ошибок: {len(result['errors'])}."
            )
            self.message_user(request, message)
            for error_msg in result["errors"]:
                self.message_user(request, error_msg, level="error")
        else:
            message = f"Процесс завершился с общей ошибкой:" f" {result['message']}"
            self.message_user(request, message)

        return HttpResponseRedirect("../")

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        old_progress = None

        if not is_new:
            old_progress = Victor.objects.get(pk=obj.pk).progress

        super().save_model(request, obj, form, change)

        calculate_user_scores(obj.username)

        update_user_hardest(obj.username)

        if is_new:
            msg = f"Игрок **{obj.username.username}** прошел **{obj.level.name}** на {obj.progress}% ({obj.device})!"
            send_discord_webhook(msg)
        elif old_progress is not None and old_progress != obj.progress:
            msg = f"📈 **Прогресс обновлен!**\nИгрок **{obj.username.username}** сделал {obj.progress}% на **{obj.level.name}** ({obj.device})!"
            send_discord_webhook(msg)

    def delete_model(self, request, obj):
        user = obj.username
        super().delete_model(request, obj)
        calculate_user_scores(user)
        update_user_hardest(user, silent=True)


@admin.register(User)
class UserAdmin(ModelAdmin):
    """Кастомные настройки для отображения пользвателей в админке"""

    list_display = ("id", "username", "region")
    search_fields = ("username", "region")
    readonly_fields = ("score_pc", "score_mobile", "hardest_pc", "hardest_mobile")
    change_list_template = "admin/user_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "update-all-scores/",
                self.admin_site.admin_view(self.update_all_scores),
                name="update_all_scores",
            )
        ]
        return custom_urls + urls

    def update_all_scores(self, request):
        if not request.user.is_superuser:
            return HttpResponseForbidden()

        users = User.objects.all()
        updated = 0
        for user in users:
            calculate_user_scores(user)
            updated += 1
        message = f"Обновлено {updated} пользователей."
        self.message_user(request, message, level=messages.SUCCESS)
        return redirect("..")


@admin.register(DiscordLink)
class DiscordLinkAdmin(ModelAdmin):
    list_display = ("auth_user", "gd_user")
    search_fields = ("username",)
    autocomplete_fields = ["auth_user", "gd_user"]


@admin.register(RecordRequest)
class RecordRequestAdmin(ModelAdmin):
    list_display = (
        "user",
        "level",
        "progress",
        "device",
        "video",
        "status",
        "created_at",
    )
    list_filter = ("status", "device")
    search_fields = ("user__username", "level__name")
    list_editable = ("status",)

    def _approve_record(self, record):
        """Логика принятия рекорда, которая раньше была в сигнале"""
        # 1. Создаем или обновляем Victor
        victor, created = Victor.objects.get_or_create(
            username=record.user,
            level=record.level,
            device=record.device,
            defaults={"progress": record.progress, "youtube": record.video},
        )

        if not created and record.progress > victor.progress:
            victor.progress = record.progress
            victor.youtube = record.video
            victor.save()

        calculate_user_scores(record.user)

        update_user_hardest(record.user)

        msg = f"🎉 **Новый рекорд принят!**\nИгрок **{record.user.username}** прошел **{record.level.name}** на {record.progress}% ({record.device})!"
        send_discord_webhook(msg)

        # Уведомление в ЛС
        notify_record_status(record, "approved", record.notes)

    def _reject_record(self, record):
        """Логика отклонения рекорда"""
        # Уведомление в ЛС
        notify_record_status(record, "rejected", record.notes)

    def _check_status_change(self, old_obj, new_obj):
        """Проверяет, изменился ли статус"""
        if old_obj.status != new_obj.status:
            if new_obj.status == "approved":
                self._approve_record(new_obj)
            elif new_obj.status == "rejected":
                self._reject_record(new_obj)

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = RecordRequest.objects.get(pk=obj.pk)
            self._check_status_change(old_obj, obj)
        else:
            if obj.status == "approved":
                self._approve_record(obj)
            elif obj.status == "rejected":
                self._reject_record(obj)

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if instance.pk:
                old_obj = RecordRequest.objects.get(pk=instance.pk)
                self._check_status_change(old_obj, instance)
            else:
                if instance.status == "approved":
                    self._approve_record(instance)
                elif instance.status == "rejected":
                    self._reject_record(instance)
            instance.save()
        formset.save_m2m()
