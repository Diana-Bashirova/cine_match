from django.db import models
from django.conf import settings


class Room(models.Model):
    code = models.CharField(max_length=50, unique=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_rooms')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_rooms', blank=True)
    invite_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # УСТАРЕВШИЕ поля — оставлены для обратной совместимости, не используются
    mood_genre = models.CharField(max_length=50, blank=True, null=True)
    max_duration = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Комната'
        verbose_name_plural = 'Комнаты'

    def __str__(self):
        return f"Room {self.code}"


class RoomMemberSettings(models.Model):
    """
    🔽 НОВАЯ МОДЕЛЬ: Личные фильтры каждого участника комнаты.
    Каждый участник может выбрать СВОИ жанры и длительность.
    """
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='member_settings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Множественный выбор жанров (хранится как JSON-массив)
    mood_genres = models.JSONField(
        default=list, 
        blank=True,
        help_text="Список выбранных жанров настроения"
    )
    max_duration = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Максимальная длительность фильма (минуты)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('room', 'user')
        verbose_name = 'Настройки участника'
        verbose_name_plural = 'Настройки участников'
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username} in {self.room.code}: {self.mood_genres}"


class RoomVote(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    vote = models.SmallIntegerField(choices=[(-1, 'Dislike'), (0, 'Skip'), (1, 'Like')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user', 'movie')
        verbose_name = 'Голос'
        verbose_name_plural = 'Голоса'