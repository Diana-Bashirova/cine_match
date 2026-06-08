from django.db import models
from django.conf import settings
from apps.movies.models import Movie

class ViewingHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewing_history')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='viewed_by')
    watched_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False, help_text="Фильм досмотрен до конца")

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-watched_at']
        verbose_name = 'Просмотр'
        verbose_name_plural = 'История просмотров'

    def __str__(self):
        return f"{self.user.username} -> {self.movie.title}"

class UserRating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='user_ratings')
    rating = models.PositiveSmallIntegerField(
        choices=[(i, f"{i}") for i in range(1, 11)],
        help_text="Оценка от 1 до 10"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки пользователей'

    def __str__(self):
        return f"{self.user.username} оценил {self.movie.title} на {self.rating}"