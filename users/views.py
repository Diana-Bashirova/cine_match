import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Профиль текущего пользователя (требует авторизации)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    Возвращает профиль авторизованного пользователя.
    Профиль создаётся автоматически сигналом post_save при регистрации.
    """
    try:
        profile = request.user.profile
        return Response({
            'username': request.user.username,
            'preference_vector': profile.preference_vector or {}
        })
    except Exception as e:
        logger.error(f"Ошибка загрузки профиля {request.user.username}: {type(e).__name__}: {e}", exc_info=True)
        return Response({'error': 'Не удалось загрузить профиль'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ─────────────────────────────────────────────────────────────────────────────
# Регистрация нового пользователя (доступно всем)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Регистрирует нового пользователя и автоматически создаёт для него профиль.
    Ожидает JSON: {"username": "...", "password": "..."}
    """
    logger.info(f"Получен запрос регистрации. Данные: {request.data}")

    # Безопасное извлечение и очистка полей
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    # Валидация входных данных
    if not username or not password:
        logger.warning("Регистрация отклонена: отсутствуют логин или пароль")
        return Response({'error': 'Логин и пароль обязательны.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(username) < 3:
        return Response({'error': 'Логин должен содержать минимум 3 символа.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 8:
        return Response({'error': 'Пароль должен содержать минимум 8 символов.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        logger.warning(f"Регистрация отклонена: пользователь '{username}' уже существует")
        return Response({'error': 'Пользователь с таким логином уже существует.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Создаём пользователя — сигнал post_save автоматически создаст профиль
        user = User.objects.create_user(username=username, password=password)
        logger.info(f"Пользователь '{username}' успешно зарегистрирован")
        return Response({
            'message': 'Регистрация успешна.',
            'username': user.username
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        # 🔍 Логируем полную информацию об ошибке для отладки
        logger.error(f"Ошибка при регистрации '{username}': {type(e).__name__}: {e}", exc_info=True)
        return Response({'error': 'Внутренняя ошибка сервера при регистрации.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)