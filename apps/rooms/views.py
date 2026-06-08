from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
import secrets
import logging

from apps.rooms.models import Room, RoomVote, RoomMemberSettings
from apps.movies.models import Movie

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Список созданных комнат",
    description="Возвращает список комнат, созданных текущим пользователем",
    responses={
        200: OpenApiResponse(
            response={'type': 'array', 'items': {'type': 'object', 'properties': {
                'id': {'type': 'integer'},
                'code': {'type': 'string'},
                'creator': {'type': 'integer'},
                'invite_link': {'type': 'string'},
                'member_count': {'type': 'integer'},
                'is_creator': {'type': 'boolean'},
                'combined_genres': {'type': 'array', 'items': {'type': 'string'}},
                'combined_max_duration': {'type': 'integer', 'nullable': True},
            }}},
            description='Список комнат'
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_rooms(request):
    """Возвращает список комнат, созданных текущим пользователем"""
    try:
        rooms = Room.objects.filter(creator=request.user, is_active=True)
        data = []
        for r in rooms:
            if not r.invite_code:
                r.invite_code = secrets.token_urlsafe(16)
                r.save(update_fields=['invite_code'])
            
            all_settings = RoomMemberSettings.objects.filter(room=r)
            total_genres = set()
            min_duration = None
            for s in all_settings:
                if s.mood_genres:
                    total_genres.update(s.mood_genres)
                if s.max_duration:
                    if min_duration is None or s.max_duration < min_duration:
                        min_duration = s.max_duration
            
            data.append({
                'id': r.id, 
                'code': r.code, 
                'creator': r.creator.id,
                'invite_link': f"http://127.0.0.1:3000/?room={r.invite_code}",
                'member_count': r.members.count(),
                'is_creator': True,
                'members': [],
                'combined_genres': sorted(list(total_genres)),
                'combined_max_duration': min_duration,
                'participants_count': all_settings.count(),
            })
        return Response(data)
    except Exception as e:
        logger.error(f"[LIST ROOMS ERROR] {e}")
        return Response({'error': 'Ошибка загрузки комнат'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Список всех комнат пользователя",
    description="Возвращает ВСЕ комнаты, где пользователь является участником (созданные + присоединённые)",
    responses={
        200: OpenApiResponse(
            response={'type': 'array', 'items': {'type': 'object', 'properties': {
                'id': {'type': 'integer'},
                'code': {'type': 'string'},
                'creator': {'type': 'integer'},
                'invite_link': {'type': 'string'},
                'member_count': {'type': 'integer'},
                'is_creator': {'type': 'boolean'},
                'combined_genres': {'type': 'array', 'items': {'type': 'string'}},
                'combined_max_duration': {'type': 'integer', 'nullable': True},
            }}},
            description='Список всех комнат пользователя'
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_rooms(request):
    """Возвращает ВСЕ комнаты, где пользователь является участником"""
    try:
        user_rooms = Room.objects.filter(
            Q(creator=request.user) | Q(members=request.user),
            is_active=True
        ).distinct()
        
        data = []
        for r in user_rooms:
            if not r.invite_code:
                r.invite_code = secrets.token_urlsafe(16)
                r.save(update_fields=['invite_code'])
            
            all_settings = RoomMemberSettings.objects.filter(room=r)
            total_genres = set()
            min_duration = None
            for s in all_settings:
                if s.mood_genres:
                    total_genres.update(s.mood_genres)
                if s.max_duration:
                    if min_duration is None or s.max_duration < min_duration:
                        min_duration = s.max_duration
            
            data.append({
                'id': r.id, 
                'code': r.code, 
                'creator': r.creator.id,
                'invite_link': f"http://127.0.0.1:3000/?room={r.invite_code}",
                'member_count': r.members.count(),
                'is_creator': r.creator.id == request.user.id,
                'members': [],
                'combined_genres': sorted(list(total_genres)),
                'combined_max_duration': min_duration,
                'participants_count': all_settings.count(),
            })
        
        return Response(data)
    except Exception as e:
        logger.error(f"[GET MY ROOMS ERROR] {e}")
        return Response({'error': 'Ошибка загрузки комнат'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Создать комнату",
    description="Создание новой комнаты для совместного подбора фильмов",
    request={'type': 'object', 'properties': {'code': {'type': 'string', 'nullable': True}}},
    responses={
        201: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'id': {'type': 'integer'},
                'code': {'type': 'string'},
                'creator': {'type': 'integer'},
                'invite_link': {'type': 'string'},
                'is_creator': {'type': 'boolean'},
                'member_count': {'type': 'integer'},
            }},
            description='Комната успешно создана'
        ),
        400: OpenApiResponse(description='Код комнаты уже занят'),
        409: OpenApiResponse(description='Конфликт - код уже существует')
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_room(request):
    """Создание новой комнаты"""
    try:
        code = request.data.get('code', '').strip()
        
        if not code:
            code = f"ROOM_{secrets.token_urlsafe(6)}"

        if Room.objects.filter(code=code).exists():
            return Response(
                {'error': f'Код "{code}" уже занят.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        invite_code = secrets.token_urlsafe(16)
        
        room = Room.objects.create(
            code=code, 
            creator=request.user, 
            invite_code=invite_code,
        )
        room.members.add(request.user)
        
        RoomMemberSettings.objects.create(
            room=room,
            user=request.user,
            mood_genres=[],
            max_duration=None,
        )

        logger.info(f"Комната '{code}' создана пользователем {request.user.username}")
        return Response({
            'id': room.id, 
            'code': room.code, 
            'creator': room.creator.id,
            'invite_link': f"http://127.0.0.1:3000/?room={room.invite_code}",
            'is_creator': True, 
            'member_count': room.members.count(),
        }, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response({'error': 'Код комнаты уже существует.'}, status=status.HTTP_409_CONFLICT)
    except Exception as e:
        logger.error(f"[CREATE ROOM ERROR] {e}", exc_info=True)
        return Response({'error': 'Внутренняя ошибка сервера.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Присоединиться к комнате",
    description="Присоединение к комнате по коду приглашения",
    request={'type': 'object', 'properties': {'invite_code': {'type': 'string'}}, 'required': ['invite_code']},
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'id': {'type': 'integer'},
                'code': {'type': 'string'},
                'creator': {'type': 'integer'},
                'invite_link': {'type': 'string'},
                'is_creator': {'type': 'boolean'},
                'member_count': {'type': 'integer'},
            }},
            description='Успешное присоединение'
        ),
        404: OpenApiResponse(description='Комната не найдена')
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_room(request):
    """Присоединение к комнате по коду приглашения"""
    invite_code = request.data.get('invite_code', '').strip()
    if not invite_code:
        return Response({'error': 'Требуется код приглашения'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = Room.objects.get(invite_code__iexact=invite_code, is_active=True)
        
        if request.user not in room.members.all():
            room.members.add(request.user)
        
        RoomMemberSettings.objects.get_or_create(
            room=room,
            user=request.user,
            defaults={'mood_genres': [], 'max_duration': None}
        )
        
        return Response({
            'id': room.id, 
            'code': room.code, 
            'creator': room.creator.id,
            'invite_link': f"http://127.0.0.1:3000/?room={room.invite_code}",
            'is_creator': request.user.id == room.creator.id,
            'member_count': room.members.count(),
        })
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена или неактивна'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[JOIN ROOM ERROR] {e}")
        return Response({'error': 'Ошибка присоединения'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Покинуть комнату",
    description="Пользователь покидает комнату (только для участников, не создателей)",
    parameters=[
        OpenApiParameter(
            name='room_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID комнаты',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {'message': {'type': 'string'}}},
            description='Вы покинули комнату'
        ),
        400: OpenApiResponse(description='Создатель не может покинуть комнату'),
        404: OpenApiResponse(description='Комната не найдена')
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_room(request, room_id):
    """Пользователь покидает комнату"""
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        if request.user.id == room.creator_id:
            return Response({'error': 'Создатель не может покинуть комнату'}, status=status.HTTP_400_BAD_REQUEST)
        
        room.members.remove(request.user)
        RoomMemberSettings.objects.filter(room=room, user=request.user).delete()
        return Response({'message': 'Вы покинули комнату'})
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Удалить комнату",
    description="Полное удаление комнаты (только для создателя)",
    parameters=[
        OpenApiParameter(
            name='room_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID комнаты',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {'message': {'type': 'string'}}},
            description='Комната удалена'
        ),
        404: OpenApiResponse(description='Комната не найдена')
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_room(request, room_id):
    """Полное удаление комнаты"""
    try:
        room = Room.objects.get(id=room_id, creator=request.user)
        original_code = room.code
        
        RoomVote.objects.filter(room=room).delete()
        RoomMemberSettings.objects.filter(room=room).delete()
        room.members.clear()
        room.delete()
        
        logger.info(f"Комната '{original_code}' удалена пользователем {request.user.username}")
        return Response({'message': f'Комната "{original_code}" удалена'}, status=status.HTTP_200_OK)
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[DELETE ROOM ERROR] {e}", exc_info=True)
        return Response({'error': 'Ошибка удаления'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Мои настройки в комнате",
    description="Получение личных настроек текущего пользователя в комнате",
    parameters=[
        OpenApiParameter(
            name='room_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID комнаты',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'mood_genres': {'type': 'array', 'items': {'type': 'string'}},
                'max_duration': {'type': 'integer', 'nullable': True},
            }},
            description='Личные настройки пользователя'
        ),
        404: OpenApiResponse(description='Комната не найдена')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_settings(request, room_id):
    """Получение личных настроек текущего пользователя в комнате"""
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        settings_obj, _ = RoomMemberSettings.objects.get_or_create(
            room=room,
            user=request.user,
            defaults={'mood_genres': [], 'max_duration': None}
        )
        return Response({
            'mood_genres': settings_obj.mood_genres or [],
            'max_duration': settings_obj.max_duration,
        })
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Обновить мои настройки",
    description="Обновление личных настроек текущего пользователя",
    parameters=[
        OpenApiParameter(
            name='room_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID комнаты',
            required=True
        )
    ],
    request={'type': 'object', 'properties': {
        'mood_genres': {'type': 'array', 'items': {'type': 'string'}},
        'max_duration': {'type': 'integer', 'nullable': True},
    }},
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'message': {'type': 'string'},
                'mood_genres': {'type': 'array', 'items': {'type': 'string'}},
                'max_duration': {'type': 'integer', 'nullable': True},
            }},
            description='Настройки обновлены'
        ),
        403: OpenApiResponse(description='Вы не участник комнаты'),
        404: OpenApiResponse(description='Комната не найдена')
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_my_settings(request, room_id):
    """Обновление личных настроек текущего пользователя"""
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        
        if request.user not in room.members.all():
            return Response({'error': 'Вы не участник комнаты'}, status=status.HTTP_403_FORBIDDEN)
        
        settings_obj, _ = RoomMemberSettings.objects.get_or_create(
            room=room,
            user=request.user,
            defaults={'mood_genres': [], 'max_duration': None}
        )
        
        mood_genres = request.data.get('mood_genres')
        max_duration = request.data.get('max_duration')
        
        if mood_genres is not None:
            if not isinstance(mood_genres, list):
                return Response({'error': 'mood_genres должен быть списком'}, status=status.HTTP_400_BAD_REQUEST)
            settings_obj.mood_genres = mood_genres
        
        if max_duration is not None:
            settings_obj.max_duration = int(max_duration) if max_duration else None
        
        settings_obj.save()
        
        logger.info(
            f"Настройки {request.user.username} в комнате '{room.code}': "
            f"жанры={settings_obj.mood_genres}, длительность={settings_obj.max_duration}"
        )
        
        return Response({
            'message': 'Настройки обновлены',
            'mood_genres': settings_obj.mood_genres,
            'max_duration': settings_obj.max_duration,
        })
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[UPDATE MY SETTINGS ERROR] {e}")
        return Response({'error': 'Ошибка обновления'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Общие настройки комнаты",
    description="Получение объединённых настроек всех участников комнаты",
    parameters=[
        OpenApiParameter(
            name='room_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID комнаты',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'combined_genres': {'type': 'array', 'items': {'type': 'string'}},
                'combined_max_duration': {'type': 'integer', 'nullable': True},
                'participants': {'type': 'array', 'items': {'type': 'object', 'properties': {
                    'user_id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'is_creator': {'type': 'boolean'},
                    'mood_genres': {'type': 'array', 'items': {'type': 'string'}},
                    'max_duration': {'type': 'integer', 'nullable': True},
                }}},
            }},
            description='Объединённые настройки всех участников'
        ),
        403: OpenApiResponse(description='Вы не участник комнаты'),
        404: OpenApiResponse(description='Комната не найдена')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_combined_settings(request, room_id):
    """Получение объединённых настроек всех участников комнаты"""
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        
        if request.user not in room.members.all():
            return Response({'error': 'Вы не участник комнаты'}, status=status.HTTP_403_FORBIDDEN)
        
        all_settings = RoomMemberSettings.objects.filter(room=room).select_related('user')
        
        combined_genres = set()
        combined_max_duration = None
        participants = []
        
        for s in all_settings:
            if s.mood_genres:
                combined_genres.update(s.mood_genres)
            if s.max_duration:
                if combined_max_duration is None or s.max_duration < combined_max_duration:
                    combined_max_duration = s.max_duration
            
            participants.append({
                'user_id': s.user.id,
                'username': s.user.username,
                'is_creator': s.user.id == room.creator_id,
                'mood_genres': s.mood_genres or [],
                'max_duration': s.max_duration,
            })
        
        return Response({
            'combined_genres': sorted(list(combined_genres)),
            'combined_max_duration': combined_max_duration,
            'participants': participants,
        })
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Список участников",
    description="Получение списка участников комнаты",
    parameters=[
        OpenApiParameter(
            name='room_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID комнаты',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'creator': {'type': 'object', 'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'is_creator': {'type': 'boolean'},
                }},
                'members': {'type': 'array', 'items': {'type': 'object', 'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                }}},
            }},
            description='Список участников комнаты'
        ),
        404: OpenApiResponse(description='Комната не найдена')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_members(request, room_id):
    """Получение списка участников"""
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        members = [
            {'id': m.id, 'username': m.username} 
            for m in room.members.all() 
            if m.id != room.creator.id
        ]
        creator = {'id': room.creator.id, 'username': room.creator.username, 'is_creator': True}
        return Response({'creator': creator, 'members': members})
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Проголосовать за фильм",
    description="Голосование за фильм в комнате (like/dislike/skip)",
    parameters=[
        OpenApiParameter(
            name='room_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID комнаты',
            required=True
        )
    ],
    request={'type': 'object', 'properties': {
        'movie_id': {'type': 'integer'},
        'vote': {'type': 'integer', 'enum': [-1, 0, 1], 'description': '-1: dislike, 0: skip, 1: like'}
    }, 'required': ['movie_id', 'vote']},
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {'status': {'type': 'string'}}},
            description='Голос принят'
        ),
        404: OpenApiResponse(description='Фильм не найден')
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote(request, room_id):
    """Голосование за фильм"""
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        movie_id = request.data.get('movie_id')
        vote_val = request.data.get('vote')
        
        if vote_val not in [-1, 0, 1]:
            return Response({'error': 'vote must be -1, 0 or 1'}, status=status.HTTP_400_BAD_REQUEST)
            
        movie = Movie.objects.get(id=movie_id)
        RoomVote.objects.update_or_create(
            room=room, user=request.user, movie=movie, 
            defaults={'vote': vote_val}
        )
        return Response({'status': 'ok'})
    except Movie.DoesNotExist:
        return Response({'error': 'Фильм не найден'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[VOTE ERROR] {e}")
        return Response({'error': 'Ошибка голосования'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="История голосов",
    description="Возвращает историю всех голосов в комнате с статистикой",
    parameters=[
        OpenApiParameter(
            name='room_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID комнаты',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(
            response={'type': 'object', 'properties': {
                'history': {'type': 'array', 'items': {'type': 'object', 'properties': {
                    'movie_id': {'type': 'integer'},
                    'movie_title': {'type': 'string'},
                    'movie_genres': {'type': 'string'},
                    'movie_duration': {'type': 'integer'},
                    'movie_rating': {'type': 'number'},
                    'votes': {'type': 'array', 'items': {'type': 'object'}},
                    'likes_count': {'type': 'integer'},
                    'dislikes_count': {'type': 'integer'},
                    'skips_count': {'type': 'integer'},
                }}},
                'stats': {'type': 'object', 'properties': {
                    'total_movies': {'type': 'integer'},
                    'total_votes': {'type': 'integer'},
                    'total_likes': {'type': 'integer'},
                    'total_dislikes': {'type': 'integer'},
                    'total_skips': {'type': 'integer'},
                }},
            }},
            description='История голосов со статистикой'
        ),
        403: OpenApiResponse(description='Вы не участник комнаты'),
        404: OpenApiResponse(description='Комната не найдена')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vote_history(request, room_id):
    """Возвращает историю всех голосов в комнате"""
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        
        if request.user not in room.members.all() and request.user != room.creator:
            return Response(
                {'error': 'Вы не участник комнаты'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        votes = RoomVote.objects.filter(room=room).select_related('movie', 'user').order_by('-created_at')
        
        movies_data = {}
        for v in votes:
            movie_id = v.movie_id
            if movie_id not in movies_data:
                movies_data[movie_id] = {
                    'movie_id': movie_id,
                    'movie_title': v.movie.title,
                    'movie_genres': v.movie.genres or '',
                    'movie_duration': v.movie.duration,
                    'movie_rating': v.movie.imdb_rating,
                    'votes': [],
                    'likes_count': 0,
                    'dislikes_count': 0,
                    'skips_count': 0,
                }
            
            vote_type = 'like' if v.vote == 1 else ('dislike' if v.vote == -1 else 'skip')
            movies_data[movie_id]['votes'].append({
                'user_id': v.user.id,
                'username': v.user.username,
                'vote': v.vote,
                'vote_type': vote_type,
                'date': v.created_at.isoformat() if v.created_at else None,
            })
            
            if v.vote == 1:
                movies_data[movie_id]['likes_count'] += 1
            elif v.vote == -1:
                movies_data[movie_id]['dislikes_count'] += 1
            else:
                movies_data[movie_id]['skips_count'] += 1
        
        result = list(movies_data.values())
        result.sort(key=lambda x: x['votes'][0]['date'] if x['votes'] else '', reverse=True)
        
        total_stats = {
            'total_movies': len(result),
            'total_votes': votes.count(),
            'total_likes': sum(m['likes_count'] for m in result),
            'total_dislikes': sum(m['dislikes_count'] for m in result),
            'total_skips': sum(m['skips_count'] for m in result),
        }
        
        return Response({
            'history': result,
            'stats': total_stats,
        })
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[GET VOTE HISTORY ERROR] {e}", exc_info=True)
        return Response(
            {'error': 'Ошибка загрузки истории голосов'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )