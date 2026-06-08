from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preference_vector = models.JSONField(default=dict, blank=True, null=True)
    
    # Timestamps с корректными значениями по умолчанию
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматически создаёт профиль при регистрации нового пользователя"""
    if created:
        try:
            # get_or_create предотвращает дубли, даже если сигнал сработает дважды
            Profile.objects.get_or_create(
                user=instance,
                defaults={
                    'preference_vector': {},
                    'created_at': timezone.now()
                }
            )
            logger.info(f"Профиль создан/найден для: {instance.username}")
        except Exception as e:
            logger.error(f"Ошибка создания профиля для {instance.username}: {e}", exc_info=True)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль при обновлении пользователя"""
    if hasattr(instance, 'profile'):
        try:
            instance.profile.save()
        except Exception as e:
            logger.error(f"Ошибка сохранения профиля для {instance.username}: {e}", exc_info=True)