from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from main.models import *
from users.models import *
# Register your models here.
admin.site.register((Product, Cart, Manufacter, CartItem, Category))
