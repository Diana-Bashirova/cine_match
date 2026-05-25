import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
from .scorer import calculate_score
from apps.rooms.models import Room, RoomVote
from apps.movies.models import Movie

logger = logging.getLogger('recommendations')

class ConsensusRequestSerializer(serializers.Serializer):
    room_id = serializers.IntegerField(help_text="ID комнаты")
    context = serializers.JSONField(required=False, default=dict, help_text="Фильтры: max_duration, min_rating")

@extend_schema(
    request=ConsensusRequestSerializer,
    responses={200: serializers.ListField(child=serializers.DictField()), 400: serializers.DictField()}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_consensus_recommendations(request):
    room_id = request.data.get('room_id')
    context = request.data.get('context', {})

    logger.info(f"Начало расчёта рекомендаций. room_id={room_id}, context={context}")

    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        logger.warning(f"Комната {room_id} не найдена")
        return Response({'error': 'Комната не найдена'}, status=404)

    user_prefs = room.creator.profile.preference_vector or {'genres': []}
    votes_by_movie = {}
    for vote in RoomVote.objects.filter(room=room):
        votes_by_movie.setdefault(vote.movie_id, []).append(vote.vote)

    movies = Movie.objects.all()
    scored = []
    for movie in movies:
        votes = votes_by_movie.get(movie.id, [])
        score = calculate_score(movie, user_prefs, context, votes)
        scored.append({'movie': movie, 'score': score})

    scored.sort(key=lambda x: x['score'], reverse=True)
    top_movies = scored[:10]

    return Response([
        {
            'movie_id': m['movie'].id,
            'title': m['movie'].title,
            'genres': m['movie'].genres,
            'duration': m['movie'].duration,
            'score': round(m['score'], 3)
        } for m in top_movies
    ])