import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordValidator:
    def validate(self, password, user=None):
        if len(password) > 128:
            raise ValidationError(
                _("Пароль слишком длинный"), code="password_too_long")
        if not re.search("[0-9]", password):
            raise ValidationError(
                _("Пароль должен содержать цифру"), code="password_no_digit")

    def get_help_text(self):
        return _(
            "Пароль должен содержать минимум 8 символов, хотя бы одну букву и одну цифру."
        )
