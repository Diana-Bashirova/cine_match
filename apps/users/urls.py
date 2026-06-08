from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.get_current_user, name='user_profile'),
    path('me/preferences/', views.update_preferences, name='update_preferences'),
    path('register/', views.register_user, name='register_user'),
]