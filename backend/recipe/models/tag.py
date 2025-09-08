from app import constants
from django.db import models
from slugify import slugify


class Tag(models.Model):
    name = models.CharField(
        max_length=constants.MAX_TAG_NAME_LENGTH,
        unique=True,
        verbose_name="Название"
    )
    slug = models.SlugField(
        max_length=constants.MAX_TAG_SLUG_LENGTH,
        unique=True,
        blank=True,
        verbose_name="Слаг"
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
