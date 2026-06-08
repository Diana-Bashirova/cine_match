# update_movies_from_tmdb.py
import os
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.models import Movie

TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '1b7b1cccec0b97653a914ca170120bbe')
TMDB_BASE = 'https://api.themoviedb.org/3'
BATCH_SIZE = 20  # Лимит запросов в секунду (бесплатный тариф)

def search_movie(title, year=None):
    """Поиск фильма по названию в TMDB"""
    params = {'api_key': TMDB_API_KEY, 'query': title, 'page': 1}
    if year:
        params['year'] = year
    try:
        resp = requests.get(f'{TMDB_BASE}/search/movie', params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get('results', [])
        return results[0] if results else None
    except Exception as e:
        print(f'❌ Ошибка поиска "{title}": {e}')
        return None

def update_movie_from_tmdb(movie):
    """Обновление объекта Movie данными из TMDB"""
    tmdb_data = search_movie(movie.title, movie.release_year)
    if not tmdb_data:
        return False
    
    # Обновляем поля
    if not movie.duration and tmdb_data.get('runtime'):
        movie.duration = tmdb_data['runtime']
    if not movie.imdb_rating and tmdb_data.get('vote_average'):
        movie.imdb_rating = round(tmdb_data['vote_average'], 1)
    if not movie.release_year and tmdb_data.get('release_date'):
        movie.release_year = int(tmdb_data['release_date'][:4])
    
    movie.save(update_fields=['duration', 'imdb_rating', 'release_year'])
    return True

def update_movies_batch(limit=100):
    """Обновление пакетом с задержкой для соблюдения лимитов API"""
    movies = Movie.objects.filter(duration__isnull=True).exclude(title__startswith='Test')[:limit]
    print(f'🔄 Начинаю обновление {movies.count()} фильмов...')
    
    for i, m in enumerate(movies, 1):
        success = update_movie_from_tmdb(m)
        status = '✅' if success else '⚠️'
        print(f'[{i}/{movies.count()}] {status} {m.title}')
        
        # Задержка, чтобы не превысить лимит TMDB (40 req/10 sec)
        if i % BATCH_SIZE == 0:
            print('⏱ Пауза 1 секунда...')
            time.sleep(1)
    
    print(f'🎬 Готово! Обновлено фильмов: {Movie.objects.exclude(duration__isnull=True).count()}')

if __name__ == '__main__':
    update_movies_batch(limit=50)  # Начните с 50 для теста