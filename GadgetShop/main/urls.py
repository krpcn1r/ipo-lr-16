from django.urls import path
from main import views

app_name = "main"

urlpatterns = [
    path("", views.url_page),
    path("about/", views.about, name="about"),
    path("shop/", views.about_shop, name="shop"),
    path("catalog/", views.product_list, name="product_list"),
    path("catalog/<int:pk>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart),
    path("cart/add/<int:product_id>", views.add_to_cart, name = "add_to_cart"),
    path("/cart/update/<int:item_id>/", views.update_cart),
    path("/cart/remove/<int:item_id>/", views.remove_from_cart),
]
 