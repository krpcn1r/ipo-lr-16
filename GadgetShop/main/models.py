from django.db import models
from PortativeGadgetShop import settings
from django.core.validators import MinLengthValidator, ValidationError
# Create your models here.


class Manufacter(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    decription = models.TextField()

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    decription = models.TextField()
    
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete = models.CASCADE, related_name="category")
    manufacter = models.ForeignKey(Manufacter, on_delete = models.CASCADE, related_name="manufacter")
    name = models.CharField(max_length=200)
    decription = models.TextField()
    photo = models.ImageField(upload_to='products/%Y/%m/%d/', blank=True,)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinLengthValidator])
    amount = models.IntegerField(validators=[MinLengthValidator])

    def __str__(self):
        return self.name
    
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"
    
    @property
    def total_cost(self):
        return sum(i.item_cost for i in self.items.all())
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product")
    amount_cart = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.__str__} ({self.amount_cart} шт.)"
    
    @property
    def item_cost(self):
        return self.product.price + self.amount_cart
    
    def clean(self):
        if(self.amount_cart > self.product.amount):
            raise ValidationError("Недостаточно товара")
        
    def start_check(self, *args, **kwargs):
        self.full_clean()
        super().clean(*args, **kwargs)