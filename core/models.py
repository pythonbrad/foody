from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator
)
from .utils import generate_restaurant_code
from django.db.models import Sum, F
import re


# Model Validators
WorkingDaysValidator = RegexValidator(r'^([0-1]{1}(\ *)){7}$')
WorkingHoursValidator = RegexValidator(
    r'^(([0-1][0-9]|2[0-3]):([0-5][0-9])-?){2}$'
)


# Models
class User(AbstractUser):
    email = models.EmailField(unique=True)
    address = models.CharField(
        max_length=64,
        help_text="Example: Malingo Junction, Buea, Cameroon"
    )
    phone_number = models.CharField(
        max_length=64,
        help_text="Example: (+237) 242 422 224"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username', 'first_name', 'last_name', 'phone_number',
        'address', 'password'
    ]

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)


class Restaurant(models.Model):
    DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    name = models.CharField(max_length=128)
    code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_restaurant_code
    )
    description = models.CharField(max_length=255, default='')
    address = models.CharField(max_length=255)
    working_days = models.CharField(
        max_length=16, validators=[WorkingDaysValidator],
        help_text=(
            'eg:\n'
            '\t0 1 1 1 1 1 1 for Mon Tue Wed Thu Fri Sat\n'
            '\t0 1 1 1 1 0 0 for Mon Tue Wed Thu\n'
        )
    )
    working_hours = models.CharField(
        max_length=16, validators=[WorkingHoursValidator],
        help_text=(
            'eg:\n'
            '\t09:30-20:00 for 09h30-20h\n'
            '\t11:00-16:39 for 11h-16h30'
        )
    )
    has_delivery = models.BooleanField(
        default=False, verbose_name='Delivery and Pick-up available?'
    )
    delivery_delay = models.PositiveSmallIntegerField(
        default=15,
        help_text='Delay in min'
    )
    pickup_delay = models.PositiveSmallIntegerField(
        default=15,
        help_text='Delay in min'
    )
    gmt = models.IntegerField(
        validators=[MinValueValidator(-12), MaxValueValidator(+12)],
        default=0
    )
    is_active = models.BooleanField(default=False)
    managers = models.ManyToManyField(
        'User', through='Manager', related_name='+'
    )
    chefs = models.ManyToManyField(
        'User', through='Chef', related_name='+'
    )
    waiters = models.ManyToManyField(
        'User', through='Waiter', related_name='+'
    )
    updated_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def toogle_state(self):
        self.is_active = not self.is_active
        self.save()

    def computed_notation(self):
        MAX_STARS = 5
        # stats
        total_marks = Book.objects.count() or 1
        marks = Book.objects.filter(
            restaurants=self
        ).count()
        score = int(MAX_STARS * marks / total_marks)
        stars = [1] * score + [0] * (MAX_STARS - score)
        return {'stars': stars, 'marks': marks}

    def computed_worktimes(self):
        # working days
        _ = re.findall(r'[0-1]{1}', self.working_days)
        working_days = {
            Restaurant.DAYS[i]: _[i] == '1' for i in range(7)
        }
        # working hours
        now = timezone.now()  # gmt +0
        now_hour = ((now.hour + self.gmt) % 24, now.minute)
        _ = re.findall(
            r'(\d+):(\d+)', self.working_hours)
        _ = (
            (int(_[0][0]), int(_[0][1])),
            (int(_[1][0]), int(_[1][1]))
        )
        working_hours = ' - '.join([
            ':'.join([
                format('%2d' % ii).replace(' ', '0')
                for ii in i
            ])
            for i in _
        ])
        # Status
        is_open = self.is_active
        is_open &= working_days[now.strftime('%a')] and _[0] < now_hour < _[1]
        return {
            'is_open': is_open,
            'working_days': working_days,
            'working_hours': working_hours
        }

    def computed_info(self):
        infos = {}
        infos.update(self.computed_notation())
        infos.update(self.computed_worktimes())
        infos['menus'] = Menu.objects.filter(entry_ref=self)
        return infos

    def save(self, *args, **kwargs):
        self.updated_date = timezone.now()
        super().save(*args, **kwargs)


class SystemConfig(models.Model):
    key = models.CharField(max_length=64)
    value = models.CharField(max_length=512)
    entry_ref = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('key', 'entry_ref')

    def __str__(self):
        return self.key

    def save(self, *args, **kwargs):
        self.key = self.key.upper()
        super().save(*args, **kwargs)


class Menu(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=255)
    items = models.ManyToManyField('Item', through='MenuItem')
    entry_ref = models.ForeignKey(
        'Restaurant',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )
    updated_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('name', 'entry_ref')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.updated_date = timezone.now()
        super().save(*args, **kwargs)


class Item(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=255)
    price = models.FloatField(default=0)
    quantity = models.PositiveSmallIntegerField(default=0)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    updated_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('name', 'category')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.updated_date = timezone.now()
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=255)
    entry_ref = models.ForeignKey(
        'Restaurant',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )

    class Meta:
        unique_together = ('name', 'entry_ref')

    def __str__(self):
        return self.name


class Order(models.Model):
    ORDER_STATUS = (
        ('d', 'Draft'),
        ('v', 'Validating'),
        ('a', 'Aborted'),
        ('w', 'Waiting'),
        ('c', 'Cooking'),
        ('r', 'Ready'),
        ('s', 'Served'),
    )
    ORDER_OPTIONS = (
        ('', 'None'),
        ('d', 'Delivery'),
        ('p', 'Pick-up')
    )
    total_price = models.FloatField(default=0)
    status = models.CharField(
        choices=ORDER_STATUS, max_length=1, default=''
    )
    ordered_date = models.DateTimeField(default=timezone.now)
    items = models.ManyToManyField(Item, through='OrderItem')
    customer = models.ForeignKey('User', on_delete=models.CASCADE)
    entry_ref = models.ForeignKey(
        'Restaurant',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )
    option = models.CharField(
        choices=ORDER_OPTIONS, max_length=1, default='d'
    )
    updated_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "Order N°%010X" % self.pk

    def add_item(self, item_pk):
        _ = Item.objects.filter(
            pk=item_pk,
            category__entry_ref=self.entry_ref
        )
        if _.exists():
            order_item = self.orderitem_set.get_or_create(
                item=_[0],
            )[0]
            order_item.quantity += 1
            order_item.save()
            self.total_price += order_item.unit_price
            self.refresh_total_price()
        else:
            pass

    def remove_item(self, orderitem_pk):
        _ = self.orderitem_set.filter(
            pk=orderitem_pk,
        )
        if _.exists():
            order_item = _[0]
            order_item.quantity -= 1
            self.total_price -= order_item.unit_price
            if order_item.quantity < 1:
                order_item.delete()
            else:
                order_item.save()
            self.refresh_total_price()
        else:
            pass

    def refresh_total_price(self):
        _ = self.orderitem_set.aggregate(
            value=Sum(F('quantity') * F('unit_price'))
        )
        self.total_price = _['value'] or 0.0
        self.save()

    def save(self, *args, **kwargs):
        self.updated_date = timezone.now()
        super().save(*args, **kwargs)


class Feedback(models.Model):
    customer = models.ForeignKey('User', on_delete=models.CASCADE)
    content = models.TextField(max_length=512)
    published_date = models.DateTimeField(default=timezone.now)
    entry_ref = models.ForeignKey(
        'Restaurant',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )

    def __str__(self):
        return self.content


class Book(models.Model):
    customer = models.OneToOneField('User', on_delete=models.CASCADE)
    restaurants = models.ManyToManyField('Restaurant', related_name='+')
    updated_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "Book of %s" % self.customer


# Intermediary model
class Manager(models.Model):
    restaurant = models.ForeignKey(
        'Restaurant',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )
    user = models.ForeignKey(
        'User',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )
    is_active = models.BooleanField(default=False)
    adhesion_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.user)


class Chef(models.Model):
    restaurant = models.ForeignKey(
        'Restaurant',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )
    user = models.ForeignKey(
        'User',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )
    is_active = models.BooleanField(default=False)
    adhesion_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.user)


class Waiter(models.Model):
    restaurant = models.ForeignKey(
        'Restaurant',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )
    user = models.ForeignKey(
        'User',
        # No backwards relations
        on_delete=models.CASCADE, related_name='+'
    )
    is_active = models.BooleanField(default=False)
    adhesion_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.user)


class MenuItem(models.Model):
    menu = models.ForeignKey('Menu', on_delete=models.CASCADE)
    item = models.ForeignKey('Item', on_delete=models.CASCADE)


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=0)
    unit_price = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        self.unit_price = self.item.price
        super().save(*args, **kwargs)
