from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Room, RoomVote
from apps.movies.models import Movie

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from rest_framework.serializers import ModelSerializer
        if self.action == 'list':
            class ListSerializer(ModelSerializer):
                class Meta:
                    model = Room
                    fields = ['id', 'code', 'creator', 'created_at']
            return ListSerializer
        class CreateSerializer(ModelSerializer):
            class Meta:
                model = Room
                fields = ['code']
            def create(self, validated_data):
                validated_data['creator'] = self.context['request'].user
                return Room.objects.create(**validated_data)
        return CreateSerializer

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        room = self.get_object()
        movie_id = request.data.get('movie_id')
        vote_val = request.data.get('vote')
        if vote_val not in [-1, 0, 1]:
            return Response({'error': 'vote must be -1, 0 or 1'}, status=400)
        movie = Movie.objects.get(id=movie_id)
        RoomVote.objects.update_or_create(
            room=room, user=request.user, movie=movie,
            defaults={'vote': vote_val}
        )
        return Response({'status': 'ok'})