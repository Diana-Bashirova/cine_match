from django.urls import path
from . import views

urlpatterns = [
    path('watched/', views.mark_watched, name='mark-watched'),
    path('ratings/', views.submit_rating, name='submit-rating'),
    path('ratings/list/', views.get_user_ratings, name='user-ratings'),
    path('ratings/<int:movie_id>/', views.delete_rating, name='delete-rating'),  # ← Это должно быть так
    path('', views.get_user_history, name='user-history'),
    path('<int:history_id>/', views.delete_history_entry, name='delete-history'),
    path('<int:history_id>/update/', views.update_history_entry, name='update-history'),
]