from rest_framework import serializers
from .models import WatchHistory
from movies.models import Movie  
from movies.serializers import MovieSerializer

class WatchHistorySerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    movie_id = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(), source='movie', write_only=True
    )
    
    class Meta:
        model = WatchHistory
        fields = ['id', 'movie', 'movie_id', 'rating', 'watched_at']
        read_only_fields = ['id', 'watched_at']