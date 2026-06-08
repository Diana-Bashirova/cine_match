from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_rooms, name='list_rooms'),
    path('my-rooms/', views.get_my_rooms, name='my_rooms'),
    path('create/', views.create_room, name='create_room'),
    path('join/', views.join_room, name='join_room'),
    path('<int:room_id>/leave/', views.leave_room, name='leave_room'),
    path('<int:room_id>/delete/', views.delete_room, name='delete_room'),
    path('<int:room_id>/members/', views.get_members, name='room_members'),
    path('<int:room_id>/vote/', views.vote, name='room_vote'),
    path('<int:room_id>/my-settings/', views.get_my_settings, name='my_settings'),
    path('<int:room_id>/my-settings/update/', views.update_my_settings, name='update_my_settings'),
    path('<int:room_id>/combined-settings/', views.get_combined_settings, name='combined_settings'),
    # 🔽 НОВОЕ: история голосов комнаты
    path('<int:room_id>/vote-history/', views.get_vote_history, name='vote_history'),
]