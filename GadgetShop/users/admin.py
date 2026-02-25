from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from main.models import *
from users.models import *
# Register your models here.

class CartInLine(admin.StackedInline):
    model = Cart
    can_delete = False
    verbose_name_plural = "Корзина"

class CustomUserAdmin(UserAdmin):
    inlines = (CartInLine, )

admin.site.register(User, UserAdmin)

