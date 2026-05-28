from .models import CartItem


def cart_count(request):
    if request.user.is_authenticated:
        total = sum(
            item.quantity
            for item in CartItem.objects.filter(cart__user=request.user)
        )
    else:
        total = 0
    return {"cart_count": total}
