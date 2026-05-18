from rest_framework import serializers
from .models import Room, RoomVote
from movies.serializers import MovieSerializer

class RoomVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomVote
        fields = ['id', 'user', 'movie', 'vote', 'voted_at']
        read_only_fields = ['id', 'voted_at']

class RoomSerializer(serializers.ModelSerializer):
    votes = RoomVoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'code', 'creator', 'context_filters', 'created_at', 'votes']
        read_only_fields = ['id', 'code', 'creator', 'created_at']