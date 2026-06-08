from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from apps.movies.models import Movie
from apps.history.models import UserRating, ViewingHistory
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_consensus_recommendations(request):
    """
    🔽 ИСПРАВЛЕНО: Справедливая формула с пороговым фильтром
    
    Логика:
    1. Минимальный порог совпадения с комнатой — 30%
    2. Веса: 60% комната + 25% лайки + 15% рейтинг
    3. Бонус +10% за 100% совпадение с комнатой
    4. Минимальный рейтинг IMDb — 5.0
    """
    try:
        room_id = request.data.get('room_id')
        if not room_id:
            return Response({'error': 'Не указан room_id'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.rooms.models import Room, RoomVote, RoomMemberSettings

        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({'error': 'Комната не найдена'}, status=status.HTTP_404_NOT_FOUND)

        # ШАГ 1: Собираем настройки ВСЕХ участников
        all_settings = RoomMemberSettings.objects.filter(room=room)
        combined_genres = set()
        combined_max_duration = None
        
        for s in all_settings:
            if s.mood_genres:
                combined_genres.update(s.mood_genres)
            if s.max_duration:
                if combined_max_duration is None or s.max_duration < combined_max_duration:
                    combined_max_duration = s.max_duration
        
        logger.info(
            f"Объединённые фильтры комнаты '{room.code}': "
            f"жанры={combined_genres or 'любые'}, длительность={combined_max_duration or 'не ограничена'}"
        )

        # ШАГ 2: Собираем голоса участников
        votes = RoomVote.objects.filter(room=room).select_related('movie')
        
        movie_scores = {}
        for v in votes:
            movie_scores[v.movie_id] = movie_scores.get(v.movie_id, 0) + v.vote
        
        voted_movie_ids = set(movie_scores.keys())

        # ШАГ 3: Базовый запрос — исключаем проголосованные
        candidates = Movie.objects.exclude(id__in=voted_movie_ids)

        # Фильтр по длительности (минимум из всех)
        if combined_max_duration:
            candidates = candidates.filter(duration__lte=int(combined_max_duration))
        
        # Фильтр по объединённым жанрам (OR)
        if combined_genres:
            genre_q = Q()
            for genre in combined_genres:
                genre_q |= Q(genres__icontains=genre.strip())
            candidates = candidates.filter(genre_q)
            logger.info(f"Кандидатов после фильтра по жанрам: {candidates.count()}")

        # 🔽 НОВОЕ: Фильтр по минимальному рейтингу IMDb (>= 5.0)
        # Отсеиваем низкокачественные фильмы
        MIN_IMDB_RATING = 5.0
        candidates = candidates.filter(
            imdb_rating__gte=MIN_IMDB_RATING,
            imdb_rating__isnull=False,
            duration__isnull=False
        )[:500]

        logger.info(
            f"Кандидатов после фильтра по рейтингу >= {MIN_IMDB_RATING}: {candidates.count()}"
        )

        # ШАГ 4: Собираем персональные предпочтения (лайки участников)
        # ВАЖНО: это отдельный набор жанров, НЕ объединяется с combined_genres
        liked_movies = votes.filter(vote=1).select_related('movie')
        personal_genres = set()
        for v in liked_movies:
            if v.movie.genres:
                for g in v.movie.genres.split(','):
                    personal_genres.add(g.strip())
        
        logger.info(f"Персональные жанры (из лайков): {personal_genres or 'нет'}")

        results = []
        skipped_count = 0
        
        for movie in candidates:
            movie_genres = set()
            if movie.genres:
                movie_genres = {g.strip() for g in movie.genres.split(',')}

            # КОМПОНЕНТ 1: Совпадение с критериями комнаты
            room_genre_overlap = len(movie_genres & combined_genres) if combined_genres else 0
            room_genre_score = (
                (room_genre_overlap / len(combined_genres) * 100) 
                if combined_genres else 50
            )
            
            # 🔽 ПОРОГОВЫЙ ФИЛЬТР: если совпадение с комнатой < 30% — пропускаем
            if combined_genres and room_genre_score < 30:
                skipped_count += 1
                continue
            
            # КОМПОНЕНТ 2: Совпадение с персональными предпочтениями
            personal_overlap = len(movie_genres & personal_genres) if personal_genres else 0
            personal_score = (
                (personal_overlap / len(personal_genres) * 100) 
                if personal_genres else 0
            )
            
            # КОМПОНЕНТ 3: Рейтинг IMDb
            rating_score = (movie.imdb_rating / 10.0) * 100 if movie.imdb_rating else 0
            
            # 🔽 НОВЫЕ ВЕСА: 60% + 25% + 15%
            final_score = (
                room_genre_score * 0.6 + 
                personal_score * 0.25 + 
                rating_score * 0.15
            )
            
            # 🔽 БОНУС за 100% совпадение с комнатой
            if combined_genres and room_genre_score == 100:
                final_score += 10
            
            final_score = round(min(100, final_score), 1)

            # Формируем объяснение
            match_reason_parts = []
            if combined_genres:
                match_reason_parts.append(
                    f"🎭 Критерии комнаты: {room_genre_overlap}/{len(combined_genres)}"
                )
            if personal_genres:
                match_reason_parts.append(
                    f"💚 Персональные: {personal_overlap}/{len(personal_genres)}"
                )
            match_reason_parts.append(f"⭐ Рейтинг: {movie.imdb_rating}")
            
            if combined_genres and room_genre_score == 100:
                match_reason_parts.append("🏆 Идеальное совпадение (+10%)")

            results.append({
                'id': movie.id,
                'title': movie.title,
                'genres': movie.genres,
                'duration': movie.duration,
                'imdb_rating': movie.imdb_rating,
                'score': final_score,
                'match_reason': ' | '.join(match_reason_parts)
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(
            f"Рекомендации для комнаты '{room.code}': "
            f"найдено {len(results)} фильмов, пропущено {skipped_count} (ниже порога)"
        )
        
        return Response(results[:10], status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Consensus recommendations error: {e}", exc_info=True)
        return Response(
            {'error': 'Ошибка расчёта рекомендаций', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_personal_recommendations(request):
    """Умные персональные рекомендации (без изменений)"""
    try:
        user = request.user

        from apps.users.models import Profile
        try:
            profile = Profile.objects.get(user=user)
            prefs = profile.preference_vector or {}
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)
            prefs = {}

        if isinstance(prefs, str):
            import json
            try:
                prefs = json.loads(prefs)
            except Exception:
                prefs = {}

        preferred_genres = prefs.get('genres', []) if isinstance(prefs, dict) else []
        if not preferred_genres:
            preferred_genres = request.data.get('genres', []) or []

        context = request.data.get('context', {}) or {}
        mood_genre = context.get('mood_genre')

        if not preferred_genres and not mood_genre:
            return Response({
                'error': 'Предпочтения не установлены.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        active_genres = [mood_genre] if mood_genre else preferred_genres

        user_ratings = UserRating.objects.filter(user=user).select_related('movie')
        watched_entries = ViewingHistory.objects.filter(user=user).select_related('movie')

        liked_movie_ids = set(user_ratings.filter(rating__gte=7).values_list('movie_id', flat=True))
        disliked_movie_ids = set(user_ratings.filter(rating__lte=3).values_list('movie_id', flat=True))
        watched_movie_ids = set(watched_entries.values_list('movie_id', flat=True))
        excluded_movie_ids = watched_movie_ids

        liked_genres = set()
        disliked_genres = set()

        if liked_movie_ids:
            for m in Movie.objects.filter(id__in=liked_movie_ids):
                if m.genres:
                    for g in m.genres.split(','):
                        liked_genres.add(g.strip())

        if disliked_movie_ids:
            for m in Movie.objects.filter(id__in=disliked_movie_ids):
                if m.genres:
                    for g in m.genres.split(','):
                        disliked_genres.add(g.strip())

        liked_genres_clean = liked_genres.copy()
        disliked_genres_clean = disliked_genres - liked_genres

        max_duration = context.get('max_duration')

        movies = Movie.objects.filter(
            imdb_rating__isnull=False,
            duration__isnull=False
        ).exclude(id__in=excluded_movie_ids)

        genre_filter = Q()
        for genre in active_genres:
            genre_filter |= Q(genres__icontains=genre.strip())
        movies = movies.filter(genre_filter)

        if max_duration:
            movies = movies.filter(duration__lte=int(max_duration))

        movies = movies.order_by('-imdb_rating')[:200]

        results = []
        for m in movies:
            movie_genres = {g.strip() for g in m.genres.split(',')} if m.genres else set()

            profile_match = movie_genres & set(active_genres)
            base_score = (len(profile_match) / len(active_genres) * 100) if active_genres else 0
            
            extra_genres = movie_genres - set(active_genres)
            extra_penalty = len(extra_genres) * 10
            profile_score = max(0, base_score - extra_penalty)

            liked_match = movie_genres & liked_genres_clean
            liked_bonus = len(liked_match) * 20 if liked_genres_clean else 0

            disliked_match = movie_genres & disliked_genres_clean
            disliked_penalty = len(disliked_match) * 40 if disliked_genres_clean else 0

            is_liked_movie = m.id in liked_movie_ids
            is_disliked_movie = m.id in disliked_movie_ids
            
            movie_rating_bonus = 0
            if is_liked_movie:
                movie_rating_bonus = 15
            elif is_disliked_movie:
                movie_rating_bonus = -30

            mood_bonus = 20 if mood_genre and mood_genre in movie_genres else 0

            if disliked_genres_clean and len(disliked_match) > len(liked_match) and len(disliked_match) >= 3:
                continue

            rating_score = (m.imdb_rating / 10.0) * 100 if m.imdb_rating else 0

            genre_component = profile_score * 0.7 + (liked_bonus - disliked_penalty) * 0.15
            final_score = round(max(0, min(100, genre_component + rating_score * 0.15 + movie_rating_bonus + mood_bonus)), 1)

            reasons = []
            if mood_genre and mood_genre in movie_genres:
                reasons.append(f"🎭 Настроение: {mood_genre} (+20%)")
            if is_liked_movie:
                reasons.append("💚 Ваш лайк (+15%)")
            if is_disliked_movie:
                reasons.append("💔 Ваш дизлайк (-30%)")
            if profile_match:
                reasons.append(f"Профиль: {', '.join(sorted(profile_match))}")
            if extra_genres:
                reasons.append(f"Лишние жанры: {', '.join(sorted(extra_genres))} (-{extra_penalty}%)")
            if liked_match and not is_liked_movie:
                reasons.append(f"Похоже на лайки: {', '.join(sorted(liked_match))}")
            if disliked_match and not is_disliked_movie:
                reasons.append(f"Похоже на дизлайки: {', '.join(sorted(disliked_match))}")

            match_reason = " | ".join(reasons) if reasons else "Общее совпадение"

            results.append({
                'id': m.id,
                'title': m.title,
                'genres': m.genres,
                'duration': m.duration,
                'imdb_rating': m.imdb_rating,
                'score': final_score,
                'match_reason': match_reason,
                'profile_match': sorted(list(profile_match)),
                'liked_match': sorted(list(liked_match)),
                'disliked_match': sorted(list(disliked_match)),
                'extra_genres': sorted(list(extra_genres)),
                'is_liked_movie': is_liked_movie,
                'is_disliked_movie': is_disliked_movie,
                'mood_genre': mood_genre,
            })

        results.sort(key=lambda x: x['score'], reverse=True)

        stats = {
            'total_liked': len(liked_movie_ids),
            'total_disliked': len(disliked_movie_ids),
            'total_watched': len(watched_movie_ids),
            'liked_genres': sorted(list(liked_genres_clean)),
            'disliked_genres': sorted(list(disliked_genres_clean)),
            'mood_genre': mood_genre,
        }

        return Response({
            'results': results[:10],
            'stats': stats,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Personal recommendations error: {e}", exc_info=True)
        return Response(
            {'error': 'Ошибка расчёта персональных рекомендаций', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )