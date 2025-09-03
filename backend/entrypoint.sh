#!/bin/sh
# Ожидание доступа к базе данных
sleep 5

# Выполняем миграции и загружаем фикстуры
python manage.py migrate
python manage.py loaddata fixtures/tags.json fixtures/ingredients.json fixtures/users.json fixtures/profiles.json fixtures/recipes.json fixtures/recipe_ingredients.json

# Запускаем сервер
exec gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 3
