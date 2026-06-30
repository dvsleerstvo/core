from django.db import models
from django.conf import settings

from .variable import STATE_CHOICES, DEVICE_CHOICES
from .utils import get_embed_url


class Level(models.Model):
    """Таблица для уровней"""

    level_id = models.PositiveIntegerField(
        unique=True, verbose_name="ID уровня в GD", blank=True, null=True
    )

    global_demonlist_id = models.PositiveIntegerField(
        verbose_name="ID уровня в глобале", blank=True, null=True
    )

    name = models.CharField(max_length=100, verbose_name="Название уровня")

    place = models.PositiveIntegerField(verbose_name="Позиция", default=0)

    published = models.CharField(max_length=100, verbose_name="Креатор", default="None")

    thumbnail_url = models.URLField(blank=True, null=True, verbose_name="Изображение")

    verifier = models.CharField(max_length=100, verbose_name="Верифер", default="None")

    creator = models.CharField(max_length=100, verbose_name="Креатор", default="None")

    description = models.CharField(
        max_length=500, verbose_name="Описание", default="None"
    )

    video = models.URLField(blank=True, null=True, verbose_name="Видео")

    completion_points_pc = models.DecimalField(
        verbose_name="Очки за прохождения(ПК)",
        decimal_places=2,
        max_digits=6,
        default=0,
    )

    list_points_pc = models.DecimalField(
        verbose_name="Очки за рекорд(ПК)", decimal_places=2, max_digits=6, default=0
    )

    list_percentage_pc = models.PositiveIntegerField(
        verbose_name="Процент листа(ПК)", default=0
    )

    completion_points_mobile = models.DecimalField(
        verbose_name="Очки за прохождения(Моб.)",
        decimal_places=2,
        max_digits=6,
        default=0,
    )

    list_points_mobile = models.FloatField(
        verbose_name="Очки за рекорд(Моб.)", default=0
    )

    list_percentage_mobile = models.PositiveIntegerField(
        verbose_name="Процент листа(Моб.)", default=0
    )

    @property
    def embed_url(self):
        return get_embed_url(self.video)

    class Meta:
        ordering = ["place"]

    def __str__(self):
        return f"{self.name}"


class User(models.Model):
    """Таблица для пользователей"""

    username = models.CharField(max_length=50, unique=True)

    global_demonlist_user_id = models.PositiveIntegerField(
        verbose_name="Id игрока в глобале",
        blank=True,
        null=True,
    )

    region = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=STATE_CHOICES,
        verbose_name="Регион",
    )

    score_pc = models.DecimalField(
        default=0, decimal_places=2, max_digits=8, verbose_name="Очки (ПК)"
    )

    score_mobile = models.DecimalField(
        default=0, decimal_places=2, max_digits=8, verbose_name="Очки (Моб.)"
    )

    hardest_pc = models.ForeignKey(
        Level,
        null=True,
        blank=True,
        related_name="users_with_pc_hardest",
        on_delete=models.SET_NULL,
        verbose_name="Сложнейший уровень на пк",
    )

    hardest_mobile = models.ForeignKey(
        Level,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users_with_mobile_hardest",
        verbose_name="Сложнейший уровень на мобиле",
    )

    gd_account_id = models.PositiveIntegerField(
        verbose_name="ID аккаунта в GD (AccountID)", blank=True, null=True, unique=True
    )

    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="Город")

    def __str__(self):
        return f"{self.username}"


class Victor(models.Model):
    """Таблица для викторов"""

    username = models.ForeignKey(User, on_delete=models.CASCADE)

    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    progress = models.PositiveIntegerField(default=0, verbose_name="Прогресс")

    device = models.CharField(
        max_length=20,
        verbose_name="Устройство",
        choices=DEVICE_CHOICES,
        null=True,
        blank=True,
    )

    youtube = models.URLField(blank=True, null=True)
    is_first_victor = models.BooleanField(
        default=False, verbose_name="Первый виктор уровня"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_first_victor:
            # Снимаем галочку у других викторов этого же уровня и устройства
            Victor.objects.filter(
                level=self.level, device=self.device, is_first_victor=True
            ).exclude(id=self.id).update(is_first_victor=False)
        super().save(*args, **kwargs)

    @property
    def embed_url(self):
        return get_embed_url(self.youtube)

    def __str__(self):
        return f"{self.level.name} - {self.username.username}"


class DiscordLink(models.Model):
    """Связывает пользователя сайта (Discord) с профилем игрока в листе"""

    auth_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discord_link",
        verbose_name="Аккаунт на сайте",
    )

    gd_user = models.OneToOneField(
        "User",
        on_delete=models.CASCADE,
        related_name="discord_link",
        verbose_name="Профиль игрока в листе",
    )

    notifications_enabled = models.BooleanField(
        default=True, verbose_name="Уведомления в ЛС"
    )

    def __str__(self):
        return f"{self.auth_user.username} <-> {self.gd_user.username}"


class RecordRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "В ожидании"),
        ("approved", "Одобрено"),
        ("rejected", "Отклонено"),
    ]

    user = models.ForeignKey("User", on_delete=models.CASCADE, verbose_name="Игрок")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, verbose_name="Уровень")
    progress = models.PositiveIntegerField(verbose_name="Прогресс", default=100)
    video = models.URLField(verbose_name="Видео (YouTube)")
    device = models.CharField(
        max_length=20, choices=DEVICE_CHOICES, verbose_name="Устройство"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Заметка модератора")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")

    class Meta:
        verbose_name = "Заявка на рекорд"
        verbose_name_plural = "Заявки на рекорды"

    def __str__(self):
        return f"[{self.get_status_display()}] {self.user.username} - {self.level.name} ({self.progress}%)"
