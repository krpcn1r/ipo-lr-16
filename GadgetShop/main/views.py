from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q, Sum, F
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def about(request):
    return HttpResponse("Зайцев Степан 89ТП 7 вариант")

def about_shop(request):
    return HttpResponse("Магазин портативных гаджетов")

def url_page(request):
    return render(request, "main/url_page.html")

def product_list(request):
    category = Category.objects.all()
    items = Product.objects.all()
    manufacter = Manufacter.objects.all()
    query = request.GET.get("q")

    category_id = request.GET.get("category")
    manufacter_id = request.GET.get("manufacter")

    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))
    
    if category_id:
        items = items.filter(category_id=category_id)

    if manufacter_id:
        items = items.filter(manufacter_id=manufacter_id)

    context = {
        'products': items,
        'categories': category,
        'manufacter': manufacter,
    }

    return render(request, "shop/product_list.html", context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "shop/product_detail.html", {'product': product})

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    new_quantity = int(request.POST.get('quantity', 1))
    
    if new_quantity == 0:
        cart_item.delete()
    elif new_quantity <= cart_item.product.amount:
        cart_item.quantity = new_quantity
        cart_item.save()
        
    return redirect('main:cart_view')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('main:cart_view')

@login_required
def cart_view(request):
    items = CartItem.objects.filter(cart__user=request.user).select_related('product')
    total_price = sum(item.item_cost for item in items)
    
    return render(request, 'shop/cart.html', {
        'items': items,
        'total_price': total_price
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=user_cart, 
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        if cart_item.quantity < product.amount:
            cart_item.quantity += 1
            cart_item.save()
    
    return redirect("main:cart_view")