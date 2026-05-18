import random, string
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Room, RoomVote
from .serializers import RoomSerializer, RoomVoteSerializer

def generate_room_code(length=6):
    """Генерация кода комнаты типа 'ABC123'"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

class RoomViewSet(viewsets.ModelViewSet):
    """Создание и управление комнатами"""
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Room.objects.filter(
            id__in=RoomVote.objects.filter(user=self.request.user).values_list('room_id', flat=True)
        ) | Room.objects.filter(creator=self.request.user)
    
    def perform_create(self, serializer):
        """При создании комнаты генерируем уникальный код"""
        code = generate_room_code()
        while Room.objects.filter(code=code).exists():
            code = generate_room_code()
        serializer.save(creator=self.request.user, code=code)
    
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """Поставить голос за фильм в комнате: POST /api/rooms/{id}/vote/"""
        room = self.get_object()
        movie_id = request.data.get('movie_id')
        vote_value = request.data.get('vote')  # -1, 0, или 1
        
        if not movie_id or vote_value is None:
            return Response({'error': 'movie_id and vote required'}, status=status.HTTP_400_BAD_REQUEST)
        
        vote, created = RoomVote.objects.update_or_create(
            room=room, user=request.user, movie_id=movie_id,
            defaults={'vote': vote_value}
        )
        return Response(RoomVoteSerializer(vote).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def state(self, request, pk=None):
        """Получить текущее состояние комнаты (для polling): GET /api/rooms/{id}/state/"""
        room = self.get_object()
        votes = RoomVote.objects.filter(room=room)
        return Response({
            'code': room.code,
            'context_filters': room.context_filters,
            'votes': RoomVoteSerializer(votes, many=True).data
        })