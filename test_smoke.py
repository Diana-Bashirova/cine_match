import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

# ─────────────────────────────────────────────────────────────────────────────
# 1. Базовая проверка БД и ORM
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_db_connection_and_user_creation():
    user = User.objects.create_user(username='ci_test', password='test123')
    assert user.username == 'ci_test'
    assert user.check_password('test123')

# ─────────────────────────────────────────────────────────────────────────────
# 2. Аутентификация (JWT)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_jwt_token_obtain():
    User.objects.create_user(username='api_user', password='securepass')
    client = APIClient()
    response = client.post('/api/token/', {'username': 'api_user', 'password': 'securepass'}, format='json')
    assert response.status_code == 200
    assert 'access' in response.data

@pytest.mark.django_db
def test_protected_endpoint_requires_auth():
    client = APIClient()
    response = client.post('/api/recommendations/consensus/', {'room_id': 1}, format='json')
    assert response.status_code == 401

# ─────────────────────────────────────────────────────────────────────────────
# 3. Юнит-тесты логики скоринга
# ─────────────────────────────────────────────────────────────────────────────
class MockMovie:
    def __init__(self, genres, duration=None, kp_rating=None, imdb_rating=None):
        self.genres = genres
        self.duration = duration
        self.kp_rating = kp_rating
        self.imdb_rating = imdb_rating

def test_scoring_genre_match_only():
    from apps.recommendations.scorer import calculate_score
    movie = MockMovie(genres=['Sci-Fi', 'Drama'])
    prefs = {'genres': ['Sci-Fi', 'Action']}
    score = calculate_score(movie, prefs, {}, [])
    assert score == pytest.approx(0.65, abs=0.01)

def test_scoring_context_penalty():
    from apps.recommendations.scorer import calculate_score
    movie = MockMovie(genres=['Action'], duration=200, kp_rating=7.0, imdb_rating=None)
    prefs = {'genres': ['Action']}
    context = {'max_duration': 150, 'min_rating': 8.0}
    score = calculate_score(movie, prefs, context, [])
    assert score == pytest.approx(0.72, abs=0.01)

def test_scoring_with_votes():
    from apps.recommendations.scorer import calculate_score
    movie = MockMovie(genres=['Comedy'], duration=90, kp_rating=8.0, imdb_rating=8.0)
    prefs = {'genres': ['Comedy']}
    score = calculate_score(movie, prefs, {}, [1, 1, -1])
    assert score == pytest.approx(0.93, abs=0.01)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Интеграционный тест /consensus/ (исправлено создание профиля)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_consensus_returns_sorted_results():
    from apps.users.models import Profile
    from apps.movies.models import Movie
    from apps.rooms.models import Room, RoomVote

    user = User.objects.create_user(username='creator', password='pass')
    user.profile.preference_vector = {'genres': ['Drama']}
    user.profile.save()

    room = Room.objects.create(code='TEST', creator=user)

    m1 = Movie.objects.create(tmdb_id=10, title='Drama Film', genres=['Drama'], duration=100, imdb_rating=8.5)
    m2 = Movie.objects.create(tmdb_id=20, title='Action Film', genres=['Action'], duration=100, imdb_rating=8.5)
    RoomVote.objects.create(room=room, user=user, movie=m1, vote=1)

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post('/api/recommendations/consensus/', {'room_id': room.id, 'context': {}}, format='json')

    assert response.status_code == 200
    assert len(response.data) >= 2
    scores = [item['score'] for item in response.data]
    assert scores == sorted(scores, reverse=True)
    assert response.data[0]['title'] == 'Drama Film'