from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Cart, CartItem, Category, Manufacter, Order, Product


class CartTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="buyer", password="pass12345"
        )
        self.category = Category.objects.create(
            name="Phones", description="Smartphones"
        )
        self.manufacter = Manufacter.objects.create(
            name="Acme", country="US", description="Vendor"
        )
        self.product = Product.objects.create(
            category=self.category,
            manufacter=self.manufacter,
            name="Acme Phone",
            description="Test phone",
            price=Decimal("10.00"),
            amount=5,
        )

    def test_cart_total_cost_uses_cart_items(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        self.assertEqual(cart.total_cost, Decimal("20.00"))

    def test_cart_item_string_uses_product_name(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        self.assertEqual(str(item), "Acme Phone (2 шт.)")

    def test_cart_item_cannot_exceed_stock(self):
        cart = Cart.objects.create(user=self.user)

        with self.assertRaises(ValidationError):
            CartItem.objects.create(cart=cart, product=self.product, quantity=6)

    def test_add_to_cart_rejects_out_of_stock_product(self):
        self.product.amount = 0
        self.product.save(update_fields=["amount"])
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("main:add_to_cart", args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CartItem.objects.exists())

    def test_checkout_decreases_stock_and_clears_cart(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_login(self.user)

        response = self.client.post(reverse("main:checkout"), {"address": "Main st."})

        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.amount, 3)
        self.assertFalse(CartItem.objects.filter(cart=cart).exists())
        self.assertEqual(Order.objects.get(user=self.user).total, Decimal("20.00"))
