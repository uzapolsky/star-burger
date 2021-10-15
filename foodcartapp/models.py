from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import DecimalField, F, Sum
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def get_order_price(self):
        return self.annotate(
            price=Sum(
                F('order_items__quantity') * F('order_items__price'),
                output_field=DecimalField(max_digits=8, decimal_places=2)
            )
        )


class Order(models.Model):
    order_statuses = [
        ('processed', 'Обработаный'),
        ('not_processed', 'Необработанный')
    ]
    payment_methods = [
        ('cash', 'Наличными'),
        ('card', 'Картой'),
        ('not_selected', 'Не выбран')
    ]
    firstname = models.CharField(
        verbose_name='имя',
        max_length=50
    )
    lastname = models.CharField(
        verbose_name='фамилия',
        max_length=50,
        blank=True
    )
    phonenumber = PhoneNumberField(
        verbose_name='телефон',
        db_index=True
    )
    address = models.CharField(
        'адрес',
        max_length=100,
    )
    order_status = models.CharField(
        verbose_name='статус',
        max_length=13,
        choices=order_statuses,
        default='not_processed',
        db_index=True
    )
    order_payment = models.CharField(
        verbose_name='оплата',
        max_length=13,
        choices=payment_methods,
        default='not_selected',
        db_index=True
    )
    comment = models.TextField(
        verbose_name='комментарий',
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name='время создания заказа',
        default=timezone.now,
        db_index=True
    )
    confirmed_at = models.DateTimeField(
        verbose_name='время подтверждения заказа',
        null=True,
        blank=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        verbose_name='время доставки заказа',
        null=True,
        blank=True,
        db_index=True
    )

    @property
    def status(self):
        return self.get_order_status_display()

    @property
    def payment(self):
        return self.get_order_payment_display()

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname} {self.address}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='order_items',
        verbose_name="заказ",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='orderes',
        verbose_name='товар',
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='количество',
    )
    price = models.DecimalField(
        verbose_name='цена',
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def __str__(self):
        return self.product.name
