from rest_framework import serializers
from django.urls import reverse
from .models import Manufacter, Category, Product, Cart, CartItem

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
