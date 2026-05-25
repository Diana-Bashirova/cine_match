from django.db import models

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=255)
    release_year = models.IntegerField(null=True, blank=True)
    genres = models.JSONField(default=list)
    duration = models.IntegerField(null=True, blank=True)
    kp_rating = models.FloatField(null=True, blank=True)
    imdb_rating = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-release_year']

    def __str__(self):
        return self.title