from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.db.models.functions import Lower
from django.contrib.auth.decorators import login_required
from .models import *


def about(request):
    return render(request, "main/about.html")


def about_shop(request):
    return render(request, "main/about_shop.html")


def home(request):
    return render(
        request,
        "main/home.html",
        {"home_categories": Category.objects.all()[:8]},
    )


def product_list(request):
    category = Category.objects.all().order_by("name")
    items = Product.objects.select_related("category", "manufacter").all().order_by("category__name", "name")

    query = (request.GET.get("q") or "").strip()
    category_id = (request.GET.get("category") or "").strip()
    raw_man_id = (request.GET.get("manufacter") or "").strip()

    if category_id:
        items = items.filter(category_id=category_id)
        manufacter_qs = (
            Manufacter.objects.filter(manufacter__category_id=category_id)
            .distinct()
            .order_by("name")
        )
    else:
        manufacter_qs = Manufacter.objects.all().order_by("name")

    allowed_man_ids = {str(m.id) for m in manufacter_qs}
    selected_man_id = raw_man_id if raw_man_id in allowed_man_ids else ""

    if query:
        q_lower = query.lower()
        items = items.annotate(
            _ln=Lower("name"),
            _ld=Lower("description"),
        ).filter(Q(_ln__contains=q_lower) | Q(_ld__contains=q_lower))

    if selected_man_id:
        items = items.filter(manufacter_id=selected_man_id)

    cart_count = 0
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(cart__user=request.user)
        cart_count = sum(item.quantity for item in cart_items)

    context = {
        "products": items,
        "categories": category,
        "manufacter": manufacter_qs,
        "selected_manufacturer_id": selected_man_id,
        "cart_count": cart_count,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        grid_html = render_to_string(
            "shop/_product_grid.html",
            context,
            request=request,
        )
        manufacturer_options_html = render_to_string(
            "shop/_manufacturer_select_options.html",
            context,
            request=request,
        )
        return JsonResponse(
            {
                "html": grid_html,
                "cart_count": cart_count,
                "manufacturer_options_html": manufacturer_options_html,
            }
        )

    return render(request, "shop/product_list.html", context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
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
