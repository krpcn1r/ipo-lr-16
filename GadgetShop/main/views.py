from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.db.models.functions import Lower
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMessage
from .forms import UserRegisterForm
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
        "main/home.html",
        {"home_categories": Category.objects.all()[:8]},
    )


def product_list(request):
    category = Category.objects.all().order_by("-is_main", "order", "name")
    items = Product.objects.select_related("category", "manufacter").all().order_by(
        "category__order", 
        "category__name",  
        "name"             
    )
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
        
        matching_ids = []
        for item in items:
            name_match = q_lower in item.name.lower()
            desc_match = item.description and q_lower in item.description.lower()
            
            if name_match or desc_match:
                matching_ids.append(item.id)
                
        items = items.filter(id__in=matching_ids)

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

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('main:login')
    else:
        form = UserRegisterForm()

    return render(request, 'main/register.html', {'form': form})