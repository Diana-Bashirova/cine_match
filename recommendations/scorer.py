# apps/recommendations/scorer.py
import logging
from django.db.models import Avg
from apps.history.models import ViewingHistory, UserRating  # Новые импорты

logger = logging.getLogger('recommendations')

def calculate_score(movie, user_prefs, context, room_votes, user=None):
    """
    Рассчитывает персонализированный скор фильма.
    
    Args:
        movie: экземпляр Movie
        user_prefs: dict с предпочтениями пользователя (например, {'genres': [...]})
        context: dict с фильтрами (max_duration, min_rating)
        room_votes: list голосов комнаты [-1, 0, 1]
        user: экземпляр User (обязателен для учёта истории/оценок)
    
    Returns:
        float: скор от 0.0 до 1.0, или -1.0 если фильм уже просмотрен
    """
    # ─────────────────────────────────────────────────────────────────────
    # 0. Быстрая фильтрация по контексту (без изменений)
    # ─────────────────────────────────────────────────────────────────────
    if context.get('max_duration') and movie.duration and movie.duration > context['max_duration']:
        return 0.0
    if context.get('min_rating'):
        rating = movie.imdb_rating or movie.kp_rating
        if rating and rating < context['min_rating']:
            return 0.0

    # ─────────────────────────────────────────────────────────────────────
    # 1. Исключаем уже просмотренные фильмы (новая логика)
    # ─────────────────────────────────────────────────────────────────────
    if user and ViewingHistory.objects.filter(user=user, movie=movie).exists():
        return -1.0  # Специальный маркер: скрыть из рекомендаций

    # ─────────────────────────────────────────────────────────────────────
    # 2. Собираем персональные данные для скоринга
    # ─────────────────────────────────────────────────────────────────────
    movie_genres = set(movie.genres or [])
    user_ratings = UserRating.objects.filter(user=user) if user else None
    
    # Жанры из фильмов, которые пользователь оценил >= 7 (сигнал "нравится")
    liked_genres = set()
    if user_ratings and user_ratings.exists():
        for r in user_ratings.filter(rating__gte=7):
            liked_genres.update(r.movie.genres or [])
    
    # Также учитываем жанры из профиля (если нет оценок)
    profile_genres = set(user_prefs.get('genres', []))
    all_liked_genres = liked_genres | profile_genres

    # ─────────────────────────────────────────────────────────────────────
    # 3. Рассчитываем компоненты скоринга
    # ─────────────────────────────────────────────────────────────────────
    
    # 3.1 Совпадение жанров (вес: 0.35)
    genre_score = 0.0
    if all_liked_genres and movie_genres:
        genre_score = len(all_liked_genres & movie_genres) / len(all_liked_genres)
    
    # 3.2 Персональный рейтинг (вес: 0.25)
    rating_score = 0.5  # fallback по умолчанию
    if user_ratings and user_ratings.exists():
        avg_personal = user_ratings.aggregate(Avg('rating'))['rating__avg'] or 5.0
        movie_rating = movie.imdb_rating or movie.kp_rating or 5.0
        # Комбинация: 60% глобальный рейтинг фильма, 40% средний рейтинг пользователя
        rating_score = (movie_rating / 10.0) * 0.6 + (avg_personal / 10.0) * 0.4
    else:
        # Если оценок нет, используем глобальный рейтинг
        movie_rating = movie.imdb_rating or movie.kp_rating or 5.0
        rating_score = movie_rating / 10.0

    # 3.3 Голоса комнаты (вес: 0.20)
    if room_votes:
        # Нормализация: [-1, 1] -> [0, 1]
        room_score = (sum(room_votes) / len(room_votes) + 1) / 2.0
    else:
        room_score = 0.5  # нейтрально, если нет голосов

    # 3.4 Доверие к персонализации (вес: 0.20)
    # Чем больше оценок у пользователя, тем больше вес его предпочтений
    personal_confidence = 0.5
    if user_ratings and user_ratings.exists():
        count = user_ratings.count()
        personal_confidence = min(1.0, count / 10.0)  # 10 оценок = максимум доверия

    # ─────────────────────────────────────────────────────────────────────
    # 4. Итоговая формула
    # ─────────────────────────────────────────────────────────────────────
    total = (
        0.35 * genre_score +
        0.25 * rating_score +
        0.20 * room_score +
        0.20 * personal_confidence
    )
    
    # Гарантируем диапазон [0.0, 1.0]
    return max(0.0, min(1.0, total))