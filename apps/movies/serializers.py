from rest_framework import serializers
from .models import Movie

class MovieSerializer(serializers.ModelSerializer):

    genres = serializers.JSONField(read_only=True)
    duration = serializers.IntegerField(allow_null=True, read_only=True)
    imdb_rating = serializers.DecimalField(max_digits=3, decimal_places=1, allow_null=True, read_only=True)
    kp_rating = serializers.DecimalField(max_digits=3, decimal_places=1, allow_null=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            'id',
            'tmdb_id',
            'title',
            'overview',
            'genres',
            'duration',
            'release_date',
            'imdb_rating',
            'kp_rating',
            'poster_url'
        ]