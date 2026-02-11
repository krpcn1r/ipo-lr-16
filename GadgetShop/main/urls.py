from django.urls import path
from main import views

app_name = "main"

urlpatterns = [
    path("", views.url_page),
    path("about/", views.about, name="about"),
    path("shop/", views.about_shop, name="shop"),
]
