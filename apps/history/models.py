from django.db import models
from django.contrib.auth.models import User

class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)
    rating = models.SmallIntegerField(null=True, blank=True)