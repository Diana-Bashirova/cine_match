from rest_framework import viewsets, permissions
from .models import Movie
from rest_framework.serializers import ModelSerializer

class MovieSerializer(ModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]