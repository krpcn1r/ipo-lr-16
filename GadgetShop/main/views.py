from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q
from .models import *
from django.contrib.auth.decorators import login_required
# Create your views here.

def about(request):
    return HttpResponse("Зайцев Степан 89ТП 7 вариант")

def about_shop(request):
    return HttpResponse("Магазин портативных гажджетов")

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
        items = items.filter(category_id = category_id)

    if manufacter_id:
        items = items.filter(manufacter_id=manufacter_id)

    context = {
        'products' : items,
        'categories' : category,
        'manufacter' : manufacter,
    }

    return render(request,"main/catalog.html", context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "main/product_detail.html", {'product':product})

def cart(request):
    pass

def update_cart(request):
    pass

def remove_from_cart(request):
    pass

def cart_view(request):
    pass

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        cart_item.amount_cart += 1
        cart_item.save()
    
    return redirect("catalog")