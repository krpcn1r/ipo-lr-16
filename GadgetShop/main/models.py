from django.db import models
from PortativeGadgetShop import settings
from django.core.validators import MinLengthValidator, ValidationError


class Manufacter(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_main = models.BooleanField(default=False, help_text="Является ли категория главной")
    order = models.PositiveIntegerField(default=100, help_text="Чем меньше число, тем выше в списке")
    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete = models.CASCADE, related_name="category")
    manufacter = models.ForeignKey(Manufacter, on_delete = models.CASCADE, related_name="manufacter")
    name = models.CharField(max_length=200)
    description = models.TextField()
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
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.__str__} ({self.quantity} шт.)"
    
    @property
    def item_cost(self):
        return self.product.price * self.quantity
    
    def clean(self):
        if(self.quantity > self.product.amount):
            raise ValidationError("Недостаточно товара")

    def start_check(self, *args, **kwargs):
        self.full_clean()
        super().clean(*args, **kwargs)


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "Новый"
        PAID = "PAID", "Оплачен"
        SHIPPED = "SHIPPED", "Отправлен"
        DONE = "DONE", "Завершён"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    address = models.CharField(max_length=255, verbose_name="Адрес доставки")
    total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Сумма"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, verbose_name="Статус"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.id} — {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} ({self.quantity} шт.)"

    @property
    def item_cost(self):
        return self.price * self.quantity