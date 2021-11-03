from collections import defaultdict

import requests
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from geopy import distance

from foodcartapp.models import Order, Product, Restaurant, RestaurantMenuItem
from places.models import Place


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    apikey = settings.YA_MAPS_API_KEY

    orders = Order.objects. \
        filter(processing_status='not_processed'). \
        order_by('-created_at'). \
        get_order_price()
    all_addresses = list(orders.values_list('address', flat=True))
    restaurants = Restaurant.objects.all()
    all_addresses.extend(list(restaurants.values_list('address', flat=True)))
    exist_addresses = list(Place.objects.all().values_list('address', flat=True))

    addresses_to_add = list(set(all_addresses) - set(exist_addresses))
    for address in addresses_to_add:
        coordinates = fetch_coordinates(apikey, address)
        if coordinates:
            lon, lat = coordinates
            Place.objects.create(
                address=address,
                lon=lon,
                lat=lat
            )
        else:
            Place.objects.create(address=address)

    restaurantmenus = RestaurantMenuItem.objects. \
        filter(availability=True). \
        select_related('product'). \
        select_related('restaurant')
    restaurants_items = defaultdict(list)
    for restaurantmenu in restaurantmenus:
        restaurants_items[restaurantmenu.restaurant].append(restaurantmenu.product.id)
    print(restaurants_items)

    places = Place.objects.all()

    order_restaurants = {}
    for order in orders:
        order_items = order.order_items.select_related('product').all()

        order_item_ids = [order_item.product.id for order_item in order_items]
        order_restaurants[order.id] = []
        for rest in restaurants_items.keys():
            if all(product in restaurants_items[rest] for product in order_item_ids):
                place_rest = places.get(address=rest.address)
                place_order = places.get(address=order.address)

                dist = round(distance.distance(
                        (place_order.lon, place_order.lat), (place_rest.lon, place_rest.lat)
                    ).km, 2)
                order_restaurants[order.id].append([rest.name, str(dist)])

    for order in order_restaurants:
        sorted_rests = sorted(order_restaurants[order], key=lambda rest: float(rest[1]))
        rests_output = [f'{rest[0]} - {rest[1]} км \n' for rest in sorted_rests]
        order_restaurants[order] = rests_output
    return render(request, template_name='order_items.html', context={
        'orders': orders, 'restaurants': order_restaurants
    })
