from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def about(request):
    return HttpResponse("Зайцев Степан 89ТП 7 вариант")

def about_shop(request):
    return HttpResponse("Магазин портативных гажджетов")

def url_page(request):
    return render(request, "main/url_page.html")