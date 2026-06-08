import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import ViewingHistory, UserRating
from .serializers import HistorySerializer, RatingSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Отметить фильм как просмотренный",
    description="Добавляет фильм в историю просмотров текущего пользователя",
    request=HistorySerializer,
    responses={
        201: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'message': {'type': 'string'},
                'created': {'type': 'boolean'}
            }},
            description='Просмотр сохранён'
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_watched(request):
    """Добавляет фильм в историю просмотров"""
    serializer = HistorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    obj, created = ViewingHistory.objects.get_or_create(
        user=request.user,
        movie_id=serializer.validated_data['movie'].id,
        defaults={'completed': serializer.validated_data.get('completed', True)}
    )
    return Response({'message': 'Просмотр сохранён', 'created': created}, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Добавить оценку фильму",
    description="Добавляет или обновляет оценку фильма текущим пользователем",
    request=RatingSerializer,
    responses={
        201: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'message': {'type': 'string'},
                'updated': {'type': 'boolean'}
            }},
            description='Оценка сохранена'
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_rating(request):
    """Добавляет или обновляет оценку фильма"""
    serializer = RatingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    obj, created = UserRating.objects.update_or_create(
        user=request.user,
        movie_id=serializer.validated_data['movie'].id,
        defaults={'rating': serializer.validated_data['rating']}
    )
    return Response({'message': 'Оценка сохранена', 'updated': not created}, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Получить мои оценки",
    description="Возвращает словарь {movie_id: rating} для предзаполнения UI",
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'additionalProperties': {'type': 'integer'}},
            description='Словарь оценок фильмов'
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_ratings(request):
    """Возвращает словарь {movie_id: rating} для предзаполнения UI"""
    ratings = UserRating.objects.filter(user=request.user).values_list('movie_id', 'rating')
    return Response(dict(ratings))


@extend_schema(
    summary="Получить историю просмотров",
    description="Возвращает историю просмотров текущего пользователя (последние 50 записей)",
    responses={
        200: OpenApiResponse(
            response=HistorySerializer(many=True),
            description='Список записей истории просмотров'
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_history(request):
    """Получить историю просмотров текущего пользователя"""
    try:
        history = ViewingHistory.objects.filter(user=request.user).select_related('movie').order_by('-watched_at')[:50]
        serializer = HistorySerializer(history, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Ошибка загрузки истории: {e}", exc_info=True)
        return Response({'error': 'Не удалось загрузить историю'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Удалить запись из истории",
    description="Удаляет запись о просмотре фильма из истории текущего пользователя",
    parameters=[
        OpenApiParameter(
            name='history_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID записи истории просмотров',
            required=True,
            examples=[
                OpenApiExample('Пример ID', value=1, summary='ID=1')
            ]
        )
    ],
    responses={
        204: OpenApiResponse(
            description='Запись успешно удалена (без тела ответа)',
            examples=[
                OpenApiExample(
                    'Успешное удаление',
                    value=None,
                    description='HTTP 204 не содержит тела ответа'
                )
            ]
        ),
        404: OpenApiResponse(
            description='Запись не найдена или недоступна',
            examples=[
                OpenApiExample(
                    'Запись не найдена',
                    value={'error': 'Запись не найдена или недоступна'},
                    description='Пример ответа при ошибке 404'
                )
            ]
        )
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_history_entry(request, history_id):
    """Удалить запись из истории просмотров"""
    try:
        entry = ViewingHistory.objects.get(id=history_id, user=request.user)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ViewingHistory.DoesNotExist:
        return Response({'error': 'Запись не найдена или недоступна'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Ошибка удаления истории {history_id}: {e}", exc_info=True)
        return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Обновить статус просмотра",
    description="Обновляет статус завершения просмотра (completed)",
    parameters=[
        OpenApiParameter(
            name='history_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID записи истории просмотров',
            required=True
        )
    ],
    request={'type': 'object', 'properties': {'completed': {'type': 'boolean'}}},
    responses={
        200: OpenApiResponse(
            response=HistorySerializer,
            description='Обновлённая запись истории'
        ),
        404: OpenApiResponse(description='Запись не найдена')
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_history_entry(request, history_id):
    """Обновить статус просмотра"""
    try:
        entry = ViewingHistory.objects.get(id=history_id, user=request.user)
        if 'completed' in request.data:
            entry.completed = bool(request.data['completed'])
            entry.save(update_fields=['completed'])
        return Response(HistorySerializer(entry).data)
    except ViewingHistory.DoesNotExist:
        return Response({'error': 'Запись не найдена или недоступна'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Ошибка обновления истории {history_id}: {e}", exc_info=True)
        return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Удалить оценку фильма",
    description="Удаляет оценку пользователя для конкретного фильма",
    parameters=[
        OpenApiParameter(
            name='movie_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID фильма',
            required=True,
            examples=[
                OpenApiExample('Пример ID фильма', value=513755, summary='ID=513755')
            ]
        )
    ],
    responses={
        204: OpenApiResponse(
            description='Оценка успешно удалена (без тела ответа)',
            examples=[
                OpenApiExample(
                    'Успешное удаление',
                    value=None,
                    description='HTTP 204 не содержит тела ответа'
                )
            ]
        ),
        404: OpenApiResponse(
            description='Оценка не найдена',
            examples=[
                OpenApiExample(
                    'Оценка не найдена',
                    value={'error': 'Оценка не найдена'},
                    description='Пример ответа при ошибке 404'
                )
            ]
        )
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_rating(request, movie_id):
    """Удаляет оценку пользователя для конкретного фильма"""
    logger.info(f"[DELETE RATING] Пользователь {request.user.username} удаляет оценку фильма {movie_id}")
    try:
        rating = UserRating.objects.get(user=request.user, movie_id=movie_id)
        rating.delete()
        logger.info(f"[DELETE RATING] ✅ Оценка фильма {movie_id} удалена")
        return Response(status=status.HTTP_204_NO_CONTENT)
    except UserRating.DoesNotExist:
        logger.warning(f"[DELETE RATING] ⚠️ Оценка фильма {movie_id} не найдена")
        return Response({'error': 'Оценка не найдена'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[DELETE RATING] ❌ Ошибка: {e}", exc_info=True)
        return Response({'error': 'Внутренняя ошибка сервера', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)