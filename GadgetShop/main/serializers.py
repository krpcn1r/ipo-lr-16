from rest_framework import serializers
from django.urls import reverse
from .models import Manufacter, Category, Product, Cart, CartItem, Order, OrderItem
from users.models import Profile

class ManufacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacter
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    manufacter_name = serializers.CharField(source='manufacter.name', read_only=True)
    detail_url = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'amount', 'photo',
            'category', 'manufacter', 'category_name', 'manufacter_name',
            'detail_url', 'in_stock',
        ]

    def get_detail_url(self, obj):
        return reverse('main:product_detail', args=[obj.id])

    def get_in_stock(self, obj):
        return obj.amount > 0

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, source='cart') # using the related_name 'cart' from CartItem

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'total_cost', 'items']


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    favorite_category_name = serializers.CharField(
        source="favorite_category.name", read_only=True, default=None
    )

    class Meta:
        model = Profile
        fields = [
            "username", "email", "role", "role_display",
            "full_name", "phone", "address",
            "favorite_category", "favorite_category_name",
            "delivery_city", "postal_code",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    item_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "price", "quantity", "item_cost"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "username", "created_at", "address", "total",
            "status", "status_display", "items",
        ]
