import logging
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Получить профиль текущего пользователя",
    description="Возвращает информацию о текущем пользователе и его предпочтения",
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'id': {'type': 'integer', 'description': 'ID пользователя'},
                'username': {'type': 'string', 'description': 'Имя пользователя'},
                'preference_vector': {
                    'type': 'object',
                    'properties': {
                        'genres': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'Список предпочитаемых жанров'
                        }
                    }
                },
            }},
            description='Профиль пользователя'
        ),
        401: OpenApiResponse(description='Не авторизован')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Возвращает профиль текущего пользователя"""
    try:
        user = request.user
        profile = getattr(user, 'profile', None)
        preference_vector = profile.preference_vector if profile else {}
        
        return Response({
            'id': user.id,
            'username': user.username,
            'preference_vector': preference_vector,
        })
    except Exception as e:
        logger.error(f"[GET USER ERROR] {e}", exc_info=True)
        return Response(
            {'error': 'Ошибка получения профиля'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Обновить предпочтения пользователя",
    description="Обновляет список предпочитаемых жанров текущего пользователя",
    request={
        'type': 'object',
        'properties': {
            'genres': {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'Список жанров',
                'example': ['Action', 'Comedy', 'Drama']
            }
        },
        'required': ['genres']
    },
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'message': {'type': 'string'},
                'genres': {
                    'type': 'array',
                    'items': {'type': 'string'}
                }
            }},
            description='Предпочтения обновлены'
        ),
        400: OpenApiResponse(description='Неверный запрос'),
        401: OpenApiResponse(description='Не авторизован')
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """Обновляет предпочтения текущего пользователя"""
    try:
        genres = request.data.get('genres')
        
        if genres is None:
            return Response(
                {'error': 'Поле genres обязательно'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(genres, list):
            return Response(
                {'error': 'genres должен быть списком'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получаем или создаем профиль
        from apps.users.models import Profile
        profile, _ = Profile.objects.get_or_create(user=request.user)
        
        # Обновляем preference_vector
        profile.preference_vector = {'genres': genres}
        profile.save(update_fields=['preference_vector'])
        
        logger.info(f"Предпочтения {request.user.username} обновлены: {genres}")
        
        return Response({
            'message': 'Предпочтения обновлены',
            'genres': genres
        })
    except Exception as e:
        logger.error(f"[UPDATE PREFERENCES ERROR] {e}", exc_info=True)
        return Response(
            {'error': 'Ошибка обновления предпочтений'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Регистрация нового пользователя",
    description="Регистрирует нового пользователя в системе",
    request={
        'type': 'object',
        'properties': {
            'username': {
                'type': 'string',
                'description': 'Имя пользователя',
                'minLength': 3,
                'example': 'newuser'
            },
            'password': {
                'type': 'string',
                'description': 'Пароль',
                'minLength': 8,
                'example': 'securepassword123'
            }
        },
        'required': ['username', 'password']
    },
    responses={
        201: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'id': {'type': 'integer'},
                'username': {'type': 'string'},
                'message': {'type': 'string'}
            }},
            description='Пользователь успешно зарегистрирован'
        ),
        400: OpenApiResponse(description='Неверные данные (короткий логин/пароль или пользователь уже существует)'),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Регистрация нового пользователя"""
    try:
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        
        if not username or not password:
            return Response(
                {'error': 'Логин и пароль обязательны'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(username) < 3:
            return Response(
                {'error': 'Логин должен содержать минимум 3 символа'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(password) < 8:
            return Response(
                {'error': 'Пароль должен содержать минимум 8 символов'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': f'Пользователь "{username}" уже существует'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(username=username, password=password)
        
        # Создаем профиль с пустыми предпочтениями
        from apps.users.models import Profile
        Profile.objects.create(user=user, preference_vector={'genres': []})
        
        logger.info(f"Зарегистрирован новый пользователь: {username}")
        
        return Response({
            'id': user.id,
            'username': user.username,
            'message': 'Регистрация успешна'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"[REGISTER ERROR] {e}", exc_info=True)
        return Response(
            {'error': 'Ошибка регистрации'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )