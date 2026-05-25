from django.urls import path
from .views import get_consensus_recommendations

urlpatterns = [
    path('consensus/', get_consensus_recommendations, name='consensus_recommendations'),
]