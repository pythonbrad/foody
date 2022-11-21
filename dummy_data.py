from core.models import (
    SystemConfig, Menu, Order, Feedback, Category, Book,
    Restaurant, User
)


def exec():
    # We create the users
    User.objects.get_or_create(
        username='julekeke',
        defaults={
            'email': 'julekeke@example.com',
            'first_name': 'Jule',
            'last_name': 'Keke',
            'password': 'secretkey',
            'address': 'Cameroon, Douala, Bonapriso',
            'phone_number': '(+237) 242 422 224'
        },
    )
    user = User.objects.get_or_create(
        username='fabojean',
        defaults={
            'email': 'fabojean@example.com',
            'first_name': 'Jean',
            'last_name': 'Fabo',
            'password': 'secretkey',
            'address': 'Cameroon, Yaounde, Ngousso',
            'phone_number': '(+237) 680 806 086',
        },
    )[0]
    user.set_password('fabojean')
    user.save()

    # We create the restaurants
    Restaurant.objects.get_or_create(
        name='TastyFood',
        defaults={
            'description': 'Come and taste',
            'address': 'Cameroon, Buea, Buea Town',
            'working_days': '0 1 1 1 1 1 1',
            'working_hours': '09:30-20:30',
        },
    )
    restaurant = Restaurant.objects.get_or_create(
        name='Foody',
        defaults={
            'description': 'Eat fine',
            'address': 'Cameroon, Buea, Malingo Junction',
            'working_days': '0111110',
            'working_hours': '09:30-15:30',
            'has_delivery': True
        },
    )[0]
    # We add managers
    restaurant.managers.add(user)
    restaurant.managers.add(
        User.objects.first()
    )
    restaurant.chefs.add(
        User.objects.get_or_create(
            username='francis', email='francis@example.com'
        )[0]
    )
    restaurant.waiters.add(
        User.objects.get_or_create(
            username='luck', email='luck@example.com'
        )[0]
    )

    # We create system configuration
    SystemConfig.objects.get_or_create(
        key='restaurant_name', entry_ref=restaurant,
        defaults={
            'value': 'Foody',
        },
    )
    SystemConfig.objects.get_or_create(
        key='restaurant_address', entry_ref=restaurant,
        defaults={
            'value': 'Buea, Malingo',
        },
    )
    SystemConfig.objects.get_or_create(
        key='restaurant_phone_number', entry_ref=restaurant,
        defaults={
            'value': '(+237) 652 72 70 95',
        },
    )

    # We create the menu
    menu = Menu.objects.get_or_create(
        name='Menu of today', entry_ref=restaurant,
        defaults={
            'description': '',
        }
    )[0]

    # We create orders
    order = Order.objects.get_or_create(
        customer=user, entry_ref=restaurant
    )[0]

    # We create categories
    category = Category.objects.get_or_create(
        name='Special', entry_ref=restaurant
    )[0]

    # We add items in the menu
    menu.items.get_or_create(
        name='Salad',
        defaults={
            'price': 1000,
            'quantity': 20,
            'category': category,
        }
    )
    menu.items.get_or_create(
        name='Ata Rice',
        defaults={
            'price': 5000,
            'quantity': 10,
            'category': category,
        }
    )
    menu.items.get_or_create(
        name='Rice and Dodo',
        defaults={
            'price': 4000,
            'quantity': 10,
            'category': category,
        }
    )
    # We add items in the order
    order.add_items(
        {item: 1 for item in menu.items.filter()}
    )

    # We create a feedback
    Feedback.objects.get_or_create(
        customer=User.objects.get_or_create(
            username='paul', email='paul@example.com'
        )[0],
        content='I like this restaurant',
        entry_ref=restaurant
    )

    # We book a restaurant
    for user in User.objects.filter():
        book = Book.objects.get_or_create(
            customer=user,
        )[0]
        book.restaurants.add(Restaurant.objects.filter().order_by('?')[0])
