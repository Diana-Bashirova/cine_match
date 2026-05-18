from rest_framework import viewsets, permissions
from .models import Movie
from .serializers import MovieSerializer

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """Только чтение: список фильмов и детали"""
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # Поиск по названию: /api/movies/?search=начало
    def get_queryset(self):
        queryset = Movie.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset