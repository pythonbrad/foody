from django.shortcuts import render, redirect, get_object_or_404
from .forms import SigninForm, LoginForm, ContactForm
from django.contrib.auth import login as _login, logout as _logout
from django.contrib.auth.decorators import login_required
from .models import (
    Category, Restaurant, Order, User
)


# Create your views here.
def index(request):
    return render(request, 'core/home.html', {
        'title': 'Home',
        'restaurants': sorted([
            (
                restaurant.computed_notation()['marks'], restaurant
            )
            for restaurant in Restaurant.objects.filter()
        ])[-4:][::-1]
    })


@login_required
def restaurants_list(request):
    return render(request, 'core/restaurants_list.html', {
        'restaurants': Restaurant.objects.filter()
    })


@login_required
def restaurants_of(request, owner):
    return render(request, 'core/restaurants_list.html', {
        'restaurants': Restaurant.objects.filter(
                owner=get_object_or_404(User, username=owner))
    })


def restaurant_page(request, code):
    restaurant = get_object_or_404(
        Restaurant, code=code)

    if request.user.is_authenticated and restaurant.has_delivery:
        customer = request.user
        order = Order.objects.get_or_create(
            status='d', customer=customer, entry_ref=restaurant
        )[0]

        if request.GET:
            if 'option' in request.GET:
                option = request.GET.get('option', None)
                if (
                    order.option != option
                    and option
                    and option in (i[0] for i in Order.ORDER_OPTIONS)
                ):
                    order.option = option
                    order.save()
                else:
                    pass
            elif 'add_item' in request.GET:
                order.add_item(request.GET.get('add_item', None))
            elif 'remove_item' in request.GET:
                order.remove_item(request.GET.get('remove_item', None))
            else:
                pass
            return redirect('core:restaurant_page', code)
        elif request.POST:
            contactform = ContactForm(request.POST)

            if contactform.is_valid():
                # If the order has item create it
                pass
            else:
                pass
        else:
            contactform = ContactForm()
    else:
        contactform = None
        order = None

    return render(request, 'core/restaurant_page.html', {
        'title': restaurant.name,
        'categories': Category.objects.filter(entry_ref=restaurant),
        'restaurant': restaurant,
        'contactform': contactform,
        'order': order
    })


def login(request):
    next_url = request.GET.get('next', '')

    if request.user.is_authenticated:
        return redirect(next_url or 'core:home')
    elif request.POST:
        form = LoginForm(request, request.POST)

        if form.is_valid():
            user = form.get_user()
            _login(request, user)
            return redirect(next_url or 'core:home')
        else:
            pass
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {
        'title': 'Login',
        'form': form,
        'next_url': next_url
    })


def signin(request):
    next_url = request.GET.get('next', '')

    if request.user.is_authenticated:
        return redirect(next_url or 'core:home')
    elif request.POST:
        form = SigninForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect(next_url or 'core:login')
        else:
            pass
    else:
        form = SigninForm()

    return render(request, 'core/signin.html', {
        'title': 'Register',
        'form': form,
        'next_url': next_url
    })


def logout(request):
    if request.user.is_authenticated:
        _logout(request)

    return redirect('core:home')
