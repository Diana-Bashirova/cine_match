from django.urls import path
from . import views

urlpatterns = [
    path('consensus/', views.get_consensus_recommendations, name='consensus-recommendations'),
    path('personal/', views.get_personal_recommendations, name='personal-recommendations'),
]