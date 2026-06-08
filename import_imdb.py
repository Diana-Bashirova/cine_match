# import_imdb.py
import os
import sys
import django
import gzip
import csv
import time
from pathlib import Path

# 🔧 Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.models import Movie

# Пути к файлам (относительно расположения скрипта)
BASE_DIR = Path(__file__).parent
BASICS_FILE = BASE_DIR / 'imdb_data' / 'title.basics.tsv'
RATINGS_FILE = BASE_DIR / 'imdb_data' / 'title.ratings.tsv'

# ⚙️ Настройки импорта
BATCH_SIZE = 2000          # Увеличен для скорости полного импорта
MIN_RATING_COUNT = 50      # Пропускать фильмы с малым числом голосов

def load_ratings():
    """Загружает рейтинги IMDb в словарь {tconst: averageRating}"""
    ratings = {}
    print(f' Загрузка рейтингов из {RATINGS_FILE}...')
    
    opener = gzip.open if RATINGS_FILE.suffix == '.gz' else open
    with opener(RATINGS_FILE, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            try:
                tconst = row['tconst']
                avg_rating = float(row['averageRating']) if row['averageRating'] != '\\N' else None
                num_votes = int(row['numVotes']) if row['numVotes'] != '\\N' else 0
                
                if num_votes >= MIN_RATING_COUNT and avg_rating is not None:
                    ratings[tconst] = round(avg_rating, 1)
            except (ValueError, KeyError):
                continue
    
    print(f'✅ Загружено {len(ratings):,} валидных рейтингов')
    return ratings

def parse_genres(genres_str):
    """Конвертирует строку жанров 'Action,Drama' в список"""
    if not genres_str or genres_str == '\\N':
        return []
    return [g.strip().title() for g in genres_str.split(',') if g.strip() and g.strip() != '\\N']

def parse_runtime(runtime_str):
    """Конвертирует длительность из строки в минуты (int)"""
    if not runtime_str or runtime_str == '\\N':
        return None
    try:
        return int(runtime_str)
    except ValueError:
        return None

def import_movies():
    """Полный импорт без ограничений по количеству"""
    if not BASICS_FILE.exists():
        print(f'❌ Файл не найден: {BASICS_FILE}')
        print('💡 Положите title.basics.tsv и title.ratings.tsv в папку imdb_data/ рядом со скриптом')
        return
    
    # Загружаем рейтинги заранее в память
    ratings_map = load_ratings()
    
    print(f'🎬 Начинаю полный импорт фильмов из {BASICS_FILE}...')
    print('⏳ Это может занять 5-15 минут в зависимости от мощности ПК...')
    
    buffer = []
    imported = 0
    skipped = 0
    start_time = time.time()
    
    opener = gzip.open if BASICS_FILE.suffix == '.gz' else open
    with opener(BASICS_FILE, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for i, row in enumerate(reader):
            try:
                # Фильтруем только фильмы (пропускаем сериалы, игры, короткометки)
                if row['titleType'] not in ('movie', 'tvMovie'):
                    skipped += 1
                    continue
                
                title = row.get('primaryTitle', '').strip()
                if not title or len(title) < 2:
                    skipped += 1
                    continue
                
                # Пропускаем контент для взрослых
                if row.get('isAdult') == '1':
                    skipped += 1
                    continue
                
                # Парсим поля
                genres = parse_genres(row.get('genres', ''))
                if not genres:  # Пропускаем фильмы без жанров
                    skipped += 1
                    continue
                
                duration = parse_runtime(row.get('runtimeMinutes', ''))
                year = int(row['startYear']) if row.get('startYear', '\\N') != '\\N' and row['startYear'].isdigit() else None
                
                # Получаем рейтинг из заранее загруженного словаря
                tconst = row['tconst']
                imdb_rating = ratings_map.get(tconst)
                
                # ✅ Создаём объект модели ТОЛЬКО с существующими полями
                buffer.append(Movie(
                    title=title,
                    release_year=year,
                    genres=', '.join(genres),
                    duration=duration,
                    imdb_rating=imdb_rating,
                    kp_rating=None,  # Кинопоиск не в IMDb
                ))
                
                # Пакетная вставка
                if len(buffer) >= BATCH_SIZE:
                    Movie.objects.bulk_create(buffer, ignore_conflicts=True)
                    imported += len(buffer)
                    print(f'📦 Вставлено {imported:,} фильмов...')
                    buffer.clear()
                
            except Exception:
                skipped += 1
                continue
    
    # Вставляем остаток
    if buffer:
        Movie.objects.bulk_create(buffer, ignore_conflicts=True)
        imported += len(buffer)
    
    elapsed = time.time() - start_time
    total = Movie.objects.count()
    print(f'\n🎉 Готово!')
    print(f'✅ Добавлено: {imported:,}')
    print(f'⏭️ Пропущено: {skipped:,} (сериалы, без жанров, 18+ и т.д.)')
    print(f'📊 Всего в БД: {total:,}')
    print(f'⏱️ Время выполнения: {elapsed/60:.1f} мин')

if __name__ == '__main__':
    import_movies()