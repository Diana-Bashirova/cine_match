from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Вектор предпочтений: { "Comedy": 0.8, "Drama": 0.3, "actors": [...], "directors": [...] }
    preference_vector = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile: {self.user.username}"
