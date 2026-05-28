from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMessage
from .models import *
import openpyxl
from io import BytesIO

def about(request):
    return render(request, "main/about.html")


def about_shop(request):
    return render(request, "main/about_shop.html")


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
    new_quantity = int(request.POST.get("quantity", 1))

    if new_quantity == 0:
        cart_item.delete()
    elif new_quantity <= cart_item.product.amount:
        cart_item.quantity = new_quantity
        cart_item.save()

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
        
        total_price = 0
        for item in cart_items:
            cost = item.item_cost 
            total_price += cost
            ws.append([item.product.name, item.quantity, float(item.product.price), float(cost)])
            
        ws.append(["", "", "ИТОГО:", float(total_price)])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        user_email = request.user.email
        if user_email:
            email = EmailMessage(
                subject="Ваш заказ в GadgetShop",
                body=f"Спасибо за заказ!\n\nАдрес доставки: {address}\nСумма: {total_price} руб.\n\nЧек в формате Excel прикреплен к этому письму.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email],
            )
            email.attach("receipt.xlsx", buffer.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            email.send(fail_silently=True)

        cart_items.delete()

        return render(request, "shop/checkout_success.html", {"email": user_email})

    total_price = sum(item.item_cost for item in cart_items)
    return render(request, "shop/checkout.html", {
        "items": cart_items, 
        "total_price": total_price
    })

# API Views
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import *


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cart_add_api(request):
    """Добавление товара в корзину через API (используется в static/js/main.js)."""
    product_id = request.data.get("product_id")
    product = get_object_or_404(Product, pk=product_id)

    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=user_cart, product=product, defaults={"quantity": 1}
    )

    if not created:
        if cart_item.quantity < product.amount:
            cart_item.quantity += 1
            cart_item.save()
        else:
            return Response(
                {"error": f"Нельзя добавить больше: на складе всего {product.amount} шт."},
                status=400,
            )

    cart_count = sum(
        i.quantity for i in CartItem.objects.filter(cart__user=request.user)
    )
    return Response(
        {
            "cart_count": cart_count,
            "message": f"«{product.name}» добавлен в корзину",
        }
    )

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ManufacterViewSet(viewsets.ModelViewSet):
    queryset = Manufacter.objects.all()
    serializer_class = ManufacterSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer