from django.db import models

class Movie(models.Model):
    tmdb_id = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=255)
    release_year = models.PositiveIntegerField(null=True, blank=True)
    genres = models.JSONField(default=list, blank=True)  # ["Comedy", "Sci-Fi"]
    directors = models.JSONField(default=list, blank=True)
    actors = models.JSONField(default=list, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)  # в минутах
    country = models.CharField(max_length=2, null=True, blank=True)
    kp_rating = models.FloatField(null=True, blank=True)
    imdb_rating = models.FloatField(null=True, blank=True)
    # Вектор для ML: { "genre_Comedy": 1, "genre_SciFi": 1, "duration_norm": 0.7, ... }
    content_vector = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.release_year})"
