from django.contrib import admin
from .models import Movie

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_year', 'duration', 'kp_rating', 'imdb_rating']
    list_filter = ['release_year', 'genres', 'country']
    search_fields = ['title', 'directors', 'actors']