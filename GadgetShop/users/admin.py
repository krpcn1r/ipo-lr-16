from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from main.models import *
from users.models import User, Profile
# Register your models here.

class CartInLine(admin.StackedInline):
    model = Cart
    can_delete = False
    extra = 0
    verbose_name_plural = "Корзина"

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    verbose_name_plural = "Профиль"

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, CartInLine)
    list_display = ("username", "email", "get_role", "is_staff")

    @admin.display(description="Роль")
    def get_role(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.get_role_display() if profile else "—"

admin.site.register(User, CustomUserAdmin)
