from django.contrib import admin
from .models import WatchHistory

@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'rating', 'watched_at']
    list_filter = ['rating', 'watched_at']
    search_fields = ['user__username', 'movie__title']