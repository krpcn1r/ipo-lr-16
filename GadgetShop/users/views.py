from django.conf import settings
from django.contrib.auth import login
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("main:product_list")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Send the check / registration confirmation email
            send_mail(
                "Регистрация в GadgetShop",
                "Вы успешно зарегистрированы! Ваш чек.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
            
            return redirect("main:product_list")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})
