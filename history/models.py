from django.db import models
from django.contrib.auth.models import User
from movies.models import Movie

class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.SmallIntegerField(null=True, blank=True)  # оценка 1-10
    watched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
        ordering = ['-watched_at']
    
    def __str__(self):
        return f"{self.user.username} → {self.movie.title} ({self.rating}/10)"
