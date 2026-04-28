from rest_framework import serializers
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
    class Meta:
        model = Product
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, source='cart') # using the related_name 'cart' from CartItem

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'total_cost', 'items']
