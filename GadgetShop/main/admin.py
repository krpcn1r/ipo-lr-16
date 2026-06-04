from django.contrib import admin
from main.models import *
# Register your models here.
admin.site.register((Product, Cart, Manufacter, CartItem, Category))


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "total", "status")
    list_filter = ("status", "created_at")
    inlines = (OrderItemInline,)
