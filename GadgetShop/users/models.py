from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Profile(models.Model):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Покупатель"
        MANAGER = "MANAGER", "Менеджер"
        ADMIN = "ADMIN", "Администратор"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CUSTOMER, verbose_name="Роль"
    )
    full_name = models.CharField(max_length=150, blank=True, verbose_name="ФИО")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.CharField(max_length=255, blank=True, verbose_name="Адрес")

    # Индивидуальные поля (вариант 7 — магазин гаджетов)
    favorite_category = models.ForeignKey(
        "main.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Любимая категория",
    )
    delivery_city = models.CharField(
        max_length=100, blank=True, verbose_name="Город доставки"
    )
    postal_code = models.CharField(
        max_length=20, blank=True, verbose_name="Почтовый индекс"
    )

    def __str__(self):
        return f"Профиль {self.user.username}"

    @property
    def is_admin(self):
        return (
            self.role == self.Role.ADMIN
            or self.user.is_staff
            or self.user.is_superuser
        )
