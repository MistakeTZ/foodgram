#!/bin/sh
set -e

# Выполняем миграции и загружаем фикстуры
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py loaddata fixtures/tags.json fixtures/ingredients.json fixtures/users.json fixtures/profiles.json fixtures/recipes.json fixtures/recipe_ingredients.json

# Передаём управление команде из CMD
exec "$@"
