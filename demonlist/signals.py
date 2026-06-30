from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Level
from .services import (update_info_from_api)

@receiver(post_save, sender=Level)
def update_level_info_on_create(sender, instance, created, **kwargs):
    """Обновление информации о уровне при создании."""
    if created:
        update_info_from_api(sender, instance, **kwargs)
