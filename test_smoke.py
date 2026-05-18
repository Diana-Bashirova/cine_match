# test_smoke.py
import pytest
from django.contrib.auth.models import User
from django.test import TestCase

@pytest.mark.django_db
def test_django_health_check():
    """Базовая проверка: Django загружается, БД подключена, модели работают"""
    # Создаём тестового пользователя
    user = User.objects.create_user(username='ci_test', password='test123')
    assert user.username == 'ci_test'
    assert user.check_password('test123')
    
    # Проверяем, что запрос к БД не падает
    assert User.objects.filter(username='ci_test').exists()