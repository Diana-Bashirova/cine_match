from django.db import models
from django.contrib.auth.models import User
from movies.models import Movie

class Room(models.Model):
    code = models.CharField(max_length=8, unique=True)  # код для приглашения, например "ABC123"
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    context_filters = models.JSONField(default=dict, blank=True)  # { "mood": "fun", "max_duration": 90, ... }
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Room {self.code} by {self.creator.username}"

class RoomVote(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    vote = models.SmallIntegerField(choices=[(-1, 'dislike'), (0, 'skip'), (1, 'like')])
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['room', 'user', 'movie']  # один пользователь — один голос за фильм в комнате