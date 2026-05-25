def calculate_score(movie, user_prefs, context, votes):
    pref_genres = user_prefs.get('genres', [])
    movie_genres = movie.genres or []
    
    genre_match = 0.0
    if pref_genres and movie_genres:
        intersection = len(set(pref_genres) & set(movie_genres))
        genre_match = intersection / len(movie_genres)

    context_score = 1.0
    max_dur = context.get('max_duration')
    min_rating = context.get('min_rating')

    if max_dur and movie.duration and movie.duration > max_dur:
        context_score -= 0.3
    
    avg_rating = 0.0
    kp = movie.kp_rating or 0
    imdb = (movie.imdb_rating or 0) / 10
    if kp or imdb:
        avg_rating = (kp + imdb) / 2
    
    if min_rating and avg_rating < min_rating:
        context_score -= 0.3

    consensus_score = 0.5
    if votes:
        avg_vote = sum(votes) / len(votes)
        consensus_score = (avg_vote + 1) / 2

    final_score = (0.5 * genre_match) + (0.3 * context_score) + (0.2 * consensus_score)
    return max(0.0, min(1.0, final_score))