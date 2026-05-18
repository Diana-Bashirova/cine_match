from recommendations.views import get_consensus_recommendations
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Импорт ViewSets
from movies.views import MovieViewSet
from users.views import UserViewSet
from rooms.views import RoomViewSet
from history.views import WatchHistoryViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'users/me', UserViewSet, basename='user-me')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'history', WatchHistoryViewSet, basename='history')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API маршруты
    path('api/', include(router.urls)),
    
    # JWT аутентификация
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
 
    path('api/recommendations/consensus/', get_consensus_recommendations, name='consensus'),   
    # Swagger документация
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]