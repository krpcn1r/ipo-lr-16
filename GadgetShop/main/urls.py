from django.contrib import admin
from django.urls import path, include
from main import views
from users import views as users_views


app_name = "main"

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/register/", users_views.register, name="register"),
    path('accounts/', include('django.contrib.auth.urls')),
    path("", views.home, name="home"),

    path("about/", views.about, name="about"),
    path("shop/", views.about_shop, name="shop"),

    path("catalog/", views.product_list, name="product_list"),
    path("catalog/<int:pk>/", views.product_detail, name="product_detail"),

    path("cart/", views.cart_view, name="cart_view"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"), 
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path("checkout/", views.checkout, name="checkout"),
]

# API URLs
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'manufacters', views.ManufacterViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'carts', views.CartViewSet, basename='cart')
router.register(r'cart-items', views.CartItemViewSet, basename='cartitem')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns += [
    path('account/', views.account_view, name='account'),
    path('account/settings/', views.settings_view, name='settings'),
    path('api/cart/add/', views.cart_add_api, name='api_cart_add'),
    path('api/me/', views.MeView.as_view(), name='api_me'),
    path('api/', include(router.urls)),
]