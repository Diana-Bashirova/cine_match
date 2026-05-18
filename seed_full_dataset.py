# seed_full_dataset.py
import os
import django
import requests
import csv
from io import StringIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from movies.models import Movie

DATASET_URL = "https://raw.githubusercontent.com/danielgrijalva/movie-stats/master/movies.csv"
BATCH_SIZE = 500  # Пакетная вставка ускоряет работу и экономит RAM

def seed_full_dataset():
    print("📥 Загрузка датасета...")
    response = requests.get(DATASET_URL)
    response.raise_for_status()

    print("🔄 Парсинг и очистка данных...")
    reader = csv.DictReader(StringIO(response.text))
    buffer = []
    total_added = 0
    base_id = 10_000_000  # Уникальный префикс, чтобы не пересекаться с ручными фильмами

    for i, row in enumerate(reader):
        try:
            title = row.get("name", "").strip()
            if not title or len(title) < 2:
                continue

            year = int(row["year"]) if row.get("year", "").isdigit() else None
            
            duration_str = row.get("minutes", "").strip()
            duration = int(float(duration_str)) if duration_str and duration_str.replace('.','',1).isdigit() else None

            rating_str = row.get("rating", "").strip()
            imdb = float(rating_str) if rating_str and rating_str.replace('.','',1).isdigit() else None

            genres_raw = row.get("genre", "")
            genres = [g.strip().title() for g in genres_raw.split(",") if g.strip()]
            if not genres:
                continue

            buffer.append(Movie(
                tmdb_id=base_id + i,
                title=title,
                release_year=year,
                genres=genres,
                duration=duration,
                kp_rating=None,
                imdb_rating=imdb
            ))

            if len(buffer) >= BATCH_SIZE:
                Movie.objects.bulk_create(buffer, ignore_conflicts=True)
                total_added += len(buffer)
                print(f"  ✅ Вставлено: {total_added}...")
                buffer.clear()

        except Exception:
            continue

    if buffer:
        Movie.objects.bulk_create(buffer, ignore_conflicts=True)
        total_added += len(buffer)

    final_count = Movie.objects.count()
    print(f"🎉 Готово! Всего фильмов в базе: {final_count}")
    if final_count < 5000:
        print("⚠️  Некоторые строки пропущены из-за пустых названий/жанров или дублей.")

if __name__ == "__main__":
    seed_full_dataset()