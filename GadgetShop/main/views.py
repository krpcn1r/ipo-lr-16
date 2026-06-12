from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMessage
from .models import *
import openpyxl
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def about(request):
    return render(request, "main/about.html")


def about_shop(request):
    return render(request, "main/about_shop.html")

def url_page(request):
    return render(request, "main/url_page.html")


def home(request):
    return render(
        request,
        "shop/index.html",
        {
            "categories": Category.objects.all().order_by("-is_main", "order", "name"),
            "popular_products": Product.objects.select_related("category", "manufacter")
            .order_by("-id")[:6],
        },
    )


def product_list(request):
    categories = Category.objects.all().order_by("-is_main", "order", "name")
    manufacturers = Manufacter.objects.all().order_by("name")

    items = Product.objects.select_related("category", "manufacter").all().order_by(
        "category__order", "category__name", "name"
    )

    query = (request.GET.get("search") or "").strip()
    category_id = (request.GET.get("category") or "").strip()
    manufacter_id = (request.GET.get("manufacter") or "").strip()

    if category_id:
        items = items.filter(category_id=category_id)
    if manufacter_id:
        items = items.filter(manufacter_id=manufacter_id)
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))

    paginator = Paginator(items, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    querystring = request.GET.copy()
    querystring.pop("page", None)

    return render(
        request,
        "shop/catalog.html",
        {
            "page_obj": page_obj,
            "products": page_obj.object_list,
            "categories": categories,
            "manufacturers": manufacturers,
            "selected_category": category_id,
            "selected_manufacter": manufacter_id,
            "search_query": query,
            "querystring": querystring.urlencode(),
        },
    )


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category", "manufacter"), pk=pk
    )
    return render(request, "shop/product_detail.html", {"product": product})


@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        new_quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        messages.error(request, "Некорректное количество товара.")
        return redirect("main:cart_view")

    if new_quantity < 0:
        messages.error(request, "Количество товара не может быть отрицательным.")
        return redirect("main:cart_view")

    if new_quantity == 0:
        cart_item.delete()
    elif new_quantity <= cart_item.product.amount:
        cart_item.quantity = new_quantity
        cart_item.save()
    else:
        messages.error(request, "Недостаточно товара на складе.")

    return redirect("main:cart_view")


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect("main:cart_view")


@login_required
def cart_view(request):
    items = CartItem.objects.filter(cart__user=request.user).select_related("product")
    total_price = sum(item.item_cost for item in items)

    return render(
        request,
        "shop/cart.html",
        {
            "items": items,
            "total_price": total_price,
        },
    )


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if product.amount <= 0:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Товара нет на складе."}, status=400)
        messages.error(request, "Товара нет на складе.")
        return redirect("main:product_detail", pk=product.pk)

    user_cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=user_cart,
        product=product,
        defaults={"quantity": 1},
    )

    if not created:
        if cart_item.quantity < product.amount:
            cart_item.quantity += 1
            cart_item.save()
        else:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"error": "Недостаточно товара на складе."}, status=400)
            messages.error(request, "Недостаточно товара на складе.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        cart_items = CartItem.objects.filter(cart__user=request.user)
        cart_count = sum(item.quantity for item in cart_items)
        return JsonResponse({"cart_count": cart_count})

    return redirect("main:cart_view")

@login_required
def checkout(request):
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=user_cart).select_related("product")

    if not cart_items.exists():
        messages.warning(request, "Ваша корзина пуста.")
        return redirect("main:cart_view")

    if request.method == "POST":
        address = request.POST.get("address")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Чек заказа"

        ws.append(["Название товара", "Количество", "Цена за шт.", "Сумма"])

        with transaction.atomic():
            cart_items = list(
                CartItem.objects.filter(cart=user_cart)
                .select_related("product")
                .select_for_update()
            )

            for item in cart_items:
                if item.quantity > item.product.amount:
                    messages.error(
                        request,
                        f"Недостаточно товара «{item.product.name}» на складе.",
                    )
                    return redirect("main:cart_view")

            order = Order.objects.create(user=request.user, address=address or "")

            total_price = 0
            for item in cart_items:
                cost = item.item_cost
                total_price += cost
                ws.append([item.product.name, item.quantity, float(item.product.price), float(cost)])
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantity,
                )
                item.product.amount -= item.quantity
                item.product.save(update_fields=["amount"])

            order.total = total_price
            order.save(update_fields=["total"])
            CartItem.objects.filter(cart=user_cart).delete()

        ws.append(["", "", "ИТОГО:", float(total_price)])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        user_email = (request.user.email or "").strip()
        email_sent = False
        if user_email:
            email = EmailMessage(
                subject="Ваш заказ в GadgetShop",
                body=f"Спасибо за заказ!\n\nАдрес доставки: {address}\nСумма: {total_price} руб.\n\nЧек в формате Excel прикреплен к этому письму.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email],
            )
            email.attach("receipt.xlsx", buffer.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            try:
                email.send(fail_silently=False)
                email_sent = True
            except Exception:
                logger.exception("Failed to send checkout receipt email to %s", user_email)
                messages.warning(
                    request,
                    "Заказ оформлен, но письмо с чеком не удалось отправить. Проверьте email или SMTP-настройки.",
                )
        else:
            messages.warning(
                request,
                "Заказ оформлен, но у аккаунта не указан email для отправки чека.",
            )

        return render(
            request,
            "shop/checkout_success.html",
            {"email": user_email, "email_sent": email_sent},
        )

    total_price = sum(item.item_cost for item in cart_items)
    return render(request, "shop/checkout.html", {
        "items": cart_items, 
        "total_price": total_price
    })


# ==========================================
# REST API ViewSets & Views (Lab 22)
# ==========================================
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .serializers import (
    CategorySerializer,
    ManufacterSerializer,
    ProductSerializer,
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
    ProfileSerializer,
)
from .permissions import IsAdminOrReadOnly, user_is_admin
from users.models import Profile


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ManufacterViewSet(viewsets.ModelViewSet):
    queryset = Manufacter.objects.all()
    serializer_class = ManufacterSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user_is_admin(user):
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cart_add_api(request):
    product_id = request.data.get('product_id')
    if not product_id:
        return Response({'error': 'Не указан ID товара.'}, status=status.HTTP_400_BAD_REQUEST)
    product = get_object_or_404(Product, pk=product_id)
    if product.amount <= 0:
        return Response({'error': 'Товара нет на складе.'}, status=status.HTTP_400_BAD_REQUEST)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        if cart_item.quantity < product.amount:
            cart_item.quantity += 1
            cart_item.save()
        else:
            return Response({'error': 'Недостаточно товара на складе.'}, status=status.HTTP_400_BAD_REQUEST)

    cart_count = sum(item.quantity for item in CartItem.objects.filter(cart=cart))
    return Response({
        'cart_count': cart_count,
        'message': 'Товар добавлен в корзину.'
    })


@login_required
def account_view(request):
    categories = Category.objects.all()
    return render(request, 'account/account.html', {'categories': categories})


@login_required
def settings_view(request):
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'email':
            email = request.POST.get('email', '').strip()
            if email:
                request.user.email = email
                request.user.save()
                messages.success(request, 'Email успешно изменен.')
            else:
                messages.error(request, 'Email не может быть пустым.')
            return redirect('main:settings')
        elif action == 'password':
            pwd_form = PasswordChangeForm(request.user, request.POST)
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно изменен.')
                return redirect('main:settings')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки при смене пароля.')
        else:
            pwd_form = PasswordChangeForm(request.user)
    else:
        pwd_form = PasswordChangeForm(request.user)

    return render(request, 'account/settings.html', {'pwd_form': pwd_form})
