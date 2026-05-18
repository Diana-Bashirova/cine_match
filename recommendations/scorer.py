# recommendations/scorer.py

def calculate_score(movie, user_prefs: dict, context: dict, votes: list) -> float:
    """
    Возвращает скор фильма от 0 до 1.
    Формула: 0.5 * вкусовое_сходство + 0.3 * контекст + 0.2 * консенсус_группы
    """
    # 1. Вкусовое сходство (пересечение жанров)
    movie_genres = set(movie.genres) if movie.genres else set()
    user_genres = set(user_prefs.get('genres', []))
    # Нормализуем: доля совпавших жанров от общего числа жанров фильма
    genre_match = len(movie_genres & user_genres) / max(len(movie_genres), 1)

    # 2. Контекстный скор (штрафы за несоответствие фильтрам)
    context_score = 1.0
    max_dur = context.get('max_duration')
    min_rating = context.get('min_rating')
    
    if max_dur and movie.duration and movie.duration > max_dur:
        context_score -= 0.3
    if min_rating:
        # Берём среднее между КП и IMDb, если оба есть
        kp = movie.kp_rating or 0
        imdb = movie.imdb_rating or 0
        avg_rating = (kp + imdb) / 2 if (kp or imdb) else 0
        if avg_rating < min_rating:
            context_score -= 0.3
    context_score = max(0.0, context_score)

    # 3. Консенсус голосов (-1..1)
    if votes:
        avg_vote = sum(votes) / len(votes)
        consensus_norm = (avg_vote + 1) / 2  # приводим к диапазону 0..1
    else:
        consensus_norm = 0.5  # нейтральный скор, если голосов нет

    # Итоговая формула
    return 0.5 * genre_match + 0.3 * context_score + 0.2 * consensus_norm