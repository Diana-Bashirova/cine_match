from rest_framework import serializers
from .models import Movie

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'tmdb_id', 'title', 'release_year', 'genres', 'directors', 
                  'actors', 'duration', 'country', 'kp_rating', 'imdb_rating']
        read_only_fields = ['id', 'tmdb_id']  # эти поля нельзя изменить через API