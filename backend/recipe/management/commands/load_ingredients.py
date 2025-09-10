import json
import pathlib

from django.core.management.base import BaseCommand

from recipe.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка ингредиентов"  # noqa: VNE003

    def handle(self, *args, **kwargs):
        Ingredient.objects.all().delete()

        data_path = pathlib.Path(
            pathlib.Path(__file__),
            "../../../data/ingredients.json",
        )

        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        ingredients = [Ingredient(**item) for item in data]
        Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"Загружено {len(ingredients)} ингредиентов"))
