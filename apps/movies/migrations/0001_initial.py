from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []  # Не зависит от других приложений
    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdb_id', models.IntegerField(unique=True)),
                ('title', models.CharField(max_length=255)),
                ('original_title', models.CharField(max_length=255, blank=True)),
                ('overview', models.TextField(blank=True)),
                ('genres', models.JSONField(blank=True, default=list)),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('release_date', models.DateField(blank=True, null=True)),
                ('poster_url', models.URLField(blank=True)),
                ('kp_rating', models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)),
                ('imdb_rating', models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Фильм',
                'verbose_name_plural': 'Фильмы',
                'ordering': ['-imdb_rating'],
            },
        ),
    ]