from django.core.management.base import BaseCommand
from ...models.ingredient import Ingredient
from os import path
import json


# Загрузка ингредиентов
class Command(BaseCommand):
    help = "Загрузка ингредиентов"

    def handle(self, *args, **kwargs):
        # Удаление всех ингредиентов
        Ingredient.objects.all().delete()

        # Загрузка ингредиентов
        data_path = path.join(
            path.dirname(__file__),
            "../../../../data/ingredients.json"
        )
        data_path = path.normpath(data_path)

        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        objs = [Ingredient(**item) for item in data]
        # Игнорирование конфликтов
        Ingredient.objects.bulk_create(objs, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"Загружено {len(objs)} ингредиентов"))
