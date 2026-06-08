from rest_framework import serializers
from .models import ViewingHistory, UserRating

class HistorySerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    class Meta:
        model = ViewingHistory
        fields = ['id', 'movie', 'movie_title', 'watched_at', 'completed']

class RatingSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    class Meta:
        model = UserRating
        fields = ['id', 'movie', 'movie_title', 'rating', 'created_at']