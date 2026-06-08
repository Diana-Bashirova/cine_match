import django
django.setup()
from apps.rooms.models import Room
from django.contrib.auth.models import User

print('=== СТРУКТУРА МОДЕЛИ ROOM ===')
for field in Room._meta.get_fields():
    print(f'- {field.name}: {type(field).__name__}')

room = Room.objects.filter(code='room_1').first()
if room:
    print(f'\n=== КОМНАТА: {room.code} ===')
    print(f'ID: {room.id}')
    print(f'Создатель: {room.creator.username}')
    
    members = room.members.all()
    print(f'\n=== УЧАСТНИКИ (members) ===')
    print(f'Количество: {members.count()}')
    for m in members:
        is_creator = (m == room.creator)
        marker = ' (СОЗДАТЕЛЬ)' if is_creator else ''
        print(f'  - {m.username}{marker}')
    
    usernames = [m.username for m in members]
    unique = set(usernames)
    print(f'\nВсего записей: {len(usernames)}')
    print(f'Уникальных: {len(unique)}')
    if len(usernames) != len(unique):
        print('НАЙДЕНЫ ДУБЛИКАТЫ!')
else:
    print('Комната room_1 не найдена')
    print('Доступные комнаты:', list(Room.objects.values_list('code', flat=True)))
