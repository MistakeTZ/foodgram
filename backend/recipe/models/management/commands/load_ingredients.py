from django.core.management.base import BaseCommand
from recipe.models.ingredient import Ingredient
from os import path
import json


class Command(BaseCommand):
    help = "Загрузка ингредиентов"

    def handle(self, *args, **kwargs):
        Ingredient.objects.all().delete()

        data_path = path.join(
            path.dirname(__file__),
            "../../../../data/ingredients.json"
        )
        data_path = path.normpath(data_path)

        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        objs = [Ingredient(**item) for item in data]
        Ingredient.objects.bulk_create(objs, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"Загружено {len(objs)} ингредиентов"))
