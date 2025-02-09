# Generated by Django 3.2 on 2021-10-15 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=100, unique=True, verbose_name='адрес')),
                ('lon', models.DecimalField(decimal_places=14, max_digits=16, verbose_name='долгота')),
                ('lat', models.DecimalField(decimal_places=14, max_digits=16, verbose_name='широта')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='дата получения координат')),
            ],
        ),
    ]
