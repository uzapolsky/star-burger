from django.db import models


class Place(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        unique=True
    )
    lon = models.DecimalField(
        max_digits=16,
        decimal_places=14,
        verbose_name='долгота',
        null=True
        )
    lat = models.DecimalField(
        max_digits=16,
        decimal_places=14,
        verbose_name='широта',
        null=True
        )
    updated_at = models.DateTimeField(
        verbose_name='дата получения координат',
        auto_now=True
    )
