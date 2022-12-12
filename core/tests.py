from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import (
    SystemConfig, Menu, Order, Feedback, Category, Book,
    Restaurant, User, WorkingDaysValidator, WorkingHoursValidator
)


# Create your tests here.
class ValidatorTest(TestCase):
    def testWorkingDaysValidator(self):
        WorkingDaysValidator('0000000')
        WorkingDaysValidator('0000001')
        WorkingDaysValidator('0 0 0 0 0 0 0')
        try:
            WorkingDaysValidator('00000000')
            WorkingDaysValidator('000000')
            WorkingDaysValidator('')
        except ValidationError:
            pass
        else:
            raise Exception()

    def testWorkingHoursValidator(self):
        WorkingHoursValidator('00:00-23:59')
        WorkingHoursValidator('00:00-23:59')
        try:
            WorkingHoursValidator('0:00-23:59')
            WorkingHoursValidator('00:0-23:59')
            WorkingHoursValidator('00:00 23:59')
            WorkingHoursValidator('')
        except ValidationError:
            pass
        else:
            raise Exception()


class UserModelTest(TestCase):
    def test_create_user(self):
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
        return User.objects.get_or_create(
            username='fabojean',
            defaults={
                'email': 'fabojean@example.com',
                'first_name': 'Jean',
                'last_name': 'Fabo',
                'password': 'secretkey',
                'address': 'Cameroon, Yaounde, Ngousso',
                'phone_number': '(+237) 680 806 086'
            },
        )[0]


class RestaurantModelTest(UserModelTest):
    def test_create_restaurant(self):
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
            },
        )[0]
        restaurant.managers.add(self.test_create_user())
        return restaurant

    def test_add_staffs(self):
        restaurant = self.test_create_restaurant()
        restaurant.managers.add(
            User.objects.get_or_create(
                username='tsogo', email='tsogo@example.com'
            )[0]
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

    def test_working_times(self):
        restaurant = self.test_create_restaurant()
        worktimes = restaurant.computed_worktimes()
        self.assertEqual(worktimes['is_open'], False)
        self.assertEqual(worktimes['working_days'], {
            'Sun': False,
            'Mon': True,
            'Tue': True,
            'Wed': True,
            'Thu': True,
            'Fri': True,
            'Sat': False
        })
        self.assertEqual(worktimes['working_hours'], '09:30 - 15:30')


class SystemConfigModelTest(RestaurantModelTest):
    def test_create_system_config(self):
        restaurant = self.test_create_restaurant()
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


class MenuModelTest(RestaurantModelTest):
    def test_create_menu(self):
        restaurant = self.test_create_restaurant()
        return Menu.objects.get_or_create(
            name='Menu of today', entry_ref=restaurant,
            defaults={
                'description': '',
            }
        )[0]


class OrderModelTest(RestaurantModelTest, UserModelTest):
    def test_create_order(self):
        restaurant = self.test_create_restaurant()
        return Order.objects.get_or_create(
            customer=self.test_create_user(), entry_ref=restaurant
        )[0]


class CategoryModelTest(RestaurantModelTest):
    def test_create_category(self):
        restaurant = self.test_create_restaurant()
        return Category.objects.get_or_create(
            name='Special', entry_ref=restaurant
        )[0]


class ItemModelTest(MenuModelTest, OrderModelTest, CategoryModelTest):
    def test_add_menu_item(self):
        menu = self.test_create_menu()
        category = self.test_create_category()
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
        return menu

    def test_add_order_item(self):
        menu = self.test_add_menu_item()
        order = self.test_create_order()
        [order.add_item(item.pk) for item in menu.items.filter()]
        order.remove_item(order.orderitem_set.first().pk)
        return order

    def test_order_total_price(self):
        order = self.test_add_order_item()
        self.assertEqual(order.total_price, 9000)
        # Test with changed item price
        # (should not affected the order already make)
        order_item = order.orderitem_set.first()
        item = order_item.item
        item.price = 100
        item.save()
        self.assertEqual(order.total_price, 9000)


class FeedbackModelTest(RestaurantModelTest, UserModelTest):
    def test_create_feedback(self):
        restaurant = self.test_create_restaurant()
        Feedback.objects.get_or_create(
            customer=User.objects.get_or_create(
                username='paul', email='paul@example.com'
            )[0],
            content='I like this restaurant',
            entry_ref=restaurant
        )


class BookModelTest(RestaurantModelTest, UserModelTest):
    def test_create_book(self):
        self.test_create_user()
        restaurant = self.test_create_restaurant()
        for user in User.objects.filter():
            book = Book.objects.get_or_create(
                customer=user,
            )[0]
            book.restaurants.add(restaurant)
        return restaurant

    def test_restaurant_notation(self):
        restaurant = self.test_create_book()
        notation = restaurant.computed_notation()
        self.assertEqual(notation['stars'], [1, 1, 1, 1, 1])
        self.assertEqual(notation['marks'], 2)
