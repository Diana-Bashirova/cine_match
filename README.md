# CineMatch Backend
AI-сервис для совместного подбора фильмов (Django + DRF + ML)

## Быстрый старт
```powershell
# 1. Клонировать и перейти в папку
git clone https://github.com/Diana-Bashirova/cine_match_backend.git
cd cine_match

# 2. Виртуальное окружение
python -m venv venv
.\venv\Scripts\activate

# 3. Зависимости и миграции
pip install -r requirements.txt
python manage.py migrate

# 4. Тестовые данные 
python seed_data.py

# 5. Запуск сервера
python manage.py runserver