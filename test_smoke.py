import pytest
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_database_connection():
    user = User.objects.create_user(username='ci_test', password='123')
    assert user.username == 'ci_test'
    assert user.check_password('123')