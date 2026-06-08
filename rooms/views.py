# apps/rooms/views.py
import logging
import re
import secrets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Room, RoomVote
from apps.movies.models import Movie
from django.db import IntegrityError

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_rooms(request):
    rooms = Room.objects.filter(creator=request.user, is_active=True)
    data = []
    for r in rooms:
        if not r.invite_code:
            r.invite_code = secrets.token_urlsafe(16)
            r.save(update_fields=['invite_code'])
        data.append({
            'id': r.id, 'code': r.code, 'creator': r.creator.id,
            'invite_link': f"http://127.0.0.1:3000/?room={r.invite_code}",
            'member_count': r.members.count() + 1,
            'is_creator': True,
            'members': []
        })
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_room(request):
    try:
        code = request.data.get('code', '').strip()
        if not code:
            # Генерируем гарантированно уникальный код
            code = f"ROOM_{secrets.token_urlsafe(6)}"

        # Проверяем уникальность СРЕДИ ВСЕХ КОМНАТ (включая удалённые)
        if Room.objects.filter(code=code).exists():
            return Response({'error': 'Код комнаты уже существует'}, status=status.HTTP_400_BAD_REQUEST)

        invite_code = secrets.token_urlsafe(16)
        room = Room.objects.create(code=code, creator=request.user, invite_code=invite_code)
        room.members.add(request.user)

        return Response({
            'id': room.id, 'code': room.code, 'creator': room.creator.id,
            'invite_link': f"http://127.0.0.1:3000/?room={room.invite_code}",
            'is_creator': True, 'member_count': 1
        }, status=status.HTTP_201_CREATED)
    except IntegrityError:
        # На случай гонки потоков: всегда возвращаем JSON, а не HTML-трейсбек
        return Response({'error': 'Код комнаты уже используется'}, status=status.HTTP_409_CONFLICT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_room(request):
    invite_code = request.data.get('invite_code', '').strip()
    
    # Если пришла полная ссылка, извлекаем чистый код
    if invite_code.startswith('http'):
        match = re.search(r'[?&]room=([^&]+)', invite_code)
        if match:
            invite_code = match.group(1)
        else:
            return Response({'error': 'Неверный формат ссылки'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not invite_code:
        return Response({'error': 'Требуется код приглашения'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Регистронезависимый поиск
        room = Room.objects.get(invite_code__iexact=invite_code, is_active=True)
        if request.user not in room.members.all() and request.user != room.creator:
            room.members.add(request.user)
        return Response({
            'id': room.id, 'code': room.code, 'creator': room.creator.id,
            'invite_link': f"http://127.0.0.1:3000/?room={room.invite_code}",
            'is_creator': request.user.id == room.creator.id,
            'member_count': room.members.count() + 1
        })
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена или неактивна'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_room(request, room_id):
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        if request.user.id == room.creator_id:
            return Response({'error': 'Создатель не может покинуть комнату'}, status=status.HTTP_400_BAD_REQUEST)
        room.members.remove(request.user)
        return Response({'message': 'Вы покинули комнату'})
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_room(request, room_id):
    try:
        room = Room.objects.get(id=room_id, creator=request.user)
        
        # 🔑 Освобождаем оригинальный код, переименовав комнату в архив
        original_code = room.code
        room.code = f"archived_{room.id}_{secrets.token_hex(4)}"
        room.is_active = False
        room.save(update_fields=['code', 'is_active'])
        
        logger.info(f"Комната '{original_code}' архивирована как '{room.code}', код '{original_code}' освобождён")
        
        return Response({'message': 'Комната архивирована, код освобождён'}, status=status.HTTP_204_NO_CONTENT)
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена или у вас нет прав'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[DELETE ERROR] {e}")
        return Response({'error': 'Ошибка при архивации'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_members(request, room_id):
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        members = [{'id': m.id, 'username': m.username} for m in room.members.all()]
        creator = {'id': room.creator.id, 'username': room.creator.username, 'is_creator': True}
        return Response({'creator': creator, 'members': members})
    except Room.DoesNotExist:
        return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote(request, room_id):
    try:
        room = Room.objects.get(id=room_id, is_active=True)
        movie_id = request.data.get('movie_id')
        vote_val = request.data.get('vote')
        if vote_val not in [-1, 0, 1]:
            return Response({'error': 'vote must be -1, 0 or 1'}, status=status.HTTP_400_BAD_REQUEST)
        movie = Movie.objects.get(id=movie_id)
        RoomVote.objects.update_or_create(room=room, user=request.user, movie=movie, defaults={'vote': vote_val})
        return Response({'status': 'ok'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)