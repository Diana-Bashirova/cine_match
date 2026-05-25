from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    code = models.CharField(max_length=10, unique=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

class RoomVote(models.Model):
    VOTE_CHOICES = ((-1, 'Dislike'), (0, 'Skip'), (1, 'Like'))
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    vote = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user', 'movie')