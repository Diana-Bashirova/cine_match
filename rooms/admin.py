from django.contrib import admin
from .models import Room, RoomVote

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['code', 'creator', 'created_at']
    search_fields = ['code']

@admin.register(RoomVote)
class RoomVoteAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'movie', 'vote', 'voted_at']
    list_filter = ['vote', 'voted_at']