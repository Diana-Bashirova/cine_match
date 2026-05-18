import os
import django
import random

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from movies.models import Movie
from rooms.models import Room, RoomVote

# 1. Список фильмов (Реалистичные данные)
MOVIES_DATA = [
    {"tmdb_id": 101, "title": "Матрица", "year": 1999, "genres": ["Фантастика", "Боевик"], "duration": 136, "kp": 8.5, "imdb": 8.7},
    {"tmdb_id": 102, "title": "Форрест Гамп", "year": 1994, "genres": ["Драма", "Комедия", "Мелодрама"], "duration": 142, "kp": 8.9, "imdb": 8.8},
    {"tmdb_id": 103, "title": "Интерстеллар", "year": 2014, "genres": ["Фантастика", "Драма"], "duration": 169, "kp": 8.6, "imdb": 8.7},
    {"tmdb_id": 104, "title": "Пятница", "year": 1995, "genres": ["Комедия"], "duration": 91, "kp": 7.5, "imdb": 6.9},
    {"tmdb_id": 105, "title": "Молчание ягнят", "year": 1991, "genres": ["Триллер", "Криминал", "Детектив"], "duration": 118, "kp": 8.3, "imdb": 8.6},
    {"tmdb_id": 106, "title": "Назад в будущее", "year": 1985, "genres": ["Фантастика", "Комедия", "Приключения"], "duration": 116, "kp": 8.6, "imdb": 8.5},
    {"tmdb_id": 107, "title": "Парк Юрского периода", "year": 1993, "genres": ["Фантастика", "Приключения"], "duration": 127, "kp": 8.1, "imdb": 8.2},
    {"tmdb_id": 108, "title": "1+1", "year": 2011, "genres": ["Драма", "Комедия", "Биография"], "duration": 112, "kp": 8.8, "imdb": 8.5},
    {"tmdb_id": 109, "title": "Джентльмены", "year": 2019, "genres": ["Боевик", "Комедия", "Криминал"], "duration": 113, "kp": 8.6, "imdb": 7.8},
    {"tmdb_id": 110, "title": "Дюна", "year": 2021, "genres": ["Фантастика", "Драма", "Приключения"], "duration": 155, "kp": 7.8, "imdb": 8.0},
    {"tmdb_id": 111, "title": "Оппенгеймер", "year": 2023, "genres": ["Биография", "Драма", "История"], "duration": 180, "kp": 8.4, "imdb": 8.5},
    {"tmdb_id": 112, "title": "Барби", "year": 2023, "genres": ["Комедия", "Фэнтези"], "duration": 114, "kp": 6.6, "imdb": 7.0},
    {"tmdb_id": 113, "title": "Бойцовский клуб", "year": 1999, "genres": ["Триллер", "Драма"], "duration": 139, "kp": 8.6, "imdb": 8.8},
    {"tmdb_id": 114, "title": "Гарри Поттер и философский камень", "year": 2001, "genres": ["Фэнтези", "Приключения"], "duration": 152, "kp": 8.2, "imdb": 7.6},
    {"tmdb_id": 115, "title": "Властелин колец: Братство кольца", "year": 2001, "genres": ["Фэнтези", "Драма", "Приключения"], "duration": 178, "kp": 8.6, "imdb": 8.8},
    {"tmdb_id": 116, "title": "Титаник", "year": 1997, "genres": ["Мелодрама", "Драма"], "duration": 194, "kp": 8.5, "imdb": 7.9},
    {"tmdb_id": 117, "title": "Аватар", "year": 2009, "genres": ["Фантастика", "Приключения"], "duration": 162, "kp": 7.8, "imdb": 7.9},
    {"tmdb_id": 118, "title": "Мстители: Финал", "year": 2019, "genres": ["Фантастика", "Боевик", "Приключения"], "duration": 181, "kp": 8.0, "imdb": 8.4},
    {"tmdb_id": 119, "title": "Паразиты", "year": 2019, "genres": ["Триллер", "Драма", "Комедия"], "duration": 132, "kp": 8.0, "imdb": 8.5},
    {"tmdb_id": 120, "title": "Джокер", "year": 2019, "genres": ["Триллер", "Драма", "Криминал"], "duration": 122, "kp": 8.2, "imdb": 8.4},
]

print("🚀 Начинаем заполнение базы данных...")

# 2. Добавление фильмов
created_count = 0
for m in MOVIES_DATA:
    obj, created = Movie.objects.update_or_create(
        tmdb_id=m['tmdb_id'],
        defaults={
            "title": m['title'],
            "release_year": m['year'],
            "genres": m['genres'],
            "duration": m['duration'],
            "kp_rating": m['kp'],
            "imdb_rating": m['imdb'],
        }
    )
    if created: created_count += 1

print(f"✅ Добавлено фильмов: {created_count}")

# 3. Создание пользователей (если их нет)
def get_user(username):
    u, _ = User.objects.get_or_create(username=username)
    return u

admin = get_user('admin')
user1 = get_user('ivan')
user2 = get_user('maria')

# Настроим им разные вкусы для интереса
admin.profile.preference_vector = {"genres": ["Фантастика", "Драма"]}
admin.profile.save()
user1.profile.preference_vector = {"genres": ["Комедия", "Боевик"]}
user1.profile.save()
user2.profile.preference_vector = {"genres": ["Триллер", "Криминал"]}
user2.profile.save()

# 4. Создание Комнаты и Голосов
print("🗳️ Генерируем голоса...")
room, _ = Room.objects.get_or_create(code="DEMO2026", defaults={"creator": admin})
RoomVote.objects.filter(room=room).delete()  # Очистить старые голоса

all_movies = list(Movie.objects.all())
users = [admin, user1, user2]

# Генерируем ~50 случайных голосов
votes_count = 0
for user in users:
    # Каждый пользователь голосует за 10-15 случайных фильмов
    voted_movies = random.sample(all_movies, min(15, len(all_movies)))
    for movie in voted_movies:
        # Случайный выбор: лайк (1), дизлайк (-1) или пропуск (0)
        vote = random.choice([1, 1, 1, -1, 0]) 
        RoomVote.objects.create(room=room, user=user, movie=movie, vote=vote)
        votes_count += 1

print(f"✅ Создана комната: {room.code}")
print(f"✅ Сгенерировано голосов: {votes_count}")
print("🎉 Готово! Можете тестировать API.")