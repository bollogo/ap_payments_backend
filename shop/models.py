import uuid
from django.db import models
from users.models import User, Wallet
from festival.models import Festival
from django.db.models import Q, F, Count, Sum, Exists, ExpressionWrapper, Case, When, Min
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.utils.crypto import get_random_string
from random import randint
import sys
from util.helper import from_ap, to_ap
from transactions import blockchain
from util.models import BaseModel, BaseQuerySet


class ShopQuerySet(BaseQuerySet):
    pass


class Shop(BaseModel):
    class Meta:
        ordering = ["-date_created"]

    serializer_class = 'ShopSerializer'

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    picture = models.CharField(max_length=255, blank=True)

    owner = models.ForeignKey(User, models.DO_NOTHING, related_name='shops')
    festival = models.ForeignKey(Festival, models.DO_NOTHING, null=True, blank=True, related_name='shops')
    pub_key = models.CharField(max_length=255)

    objects = ShopQuerySet.as_manager()

    @property
    def unfulfilled_order_count(self):
        return self.orders.unfulfilled().count()
    
    @property
    def ready_order_count(self):
        return self.orders.ready().count()

    @property
    def recent_orders(self):
        return self.orders.order_by('-date_created', 'id')[:4]

    @property
    def orders_to_fulfill(self):
        return (self.orders.filter(
            Q(status__in=['paid', 'ready']) |
            Q(status__in=['pending'], date_updated__gt=timezone.now() - timedelta(minutes=5)) |
            Q(status='success', date_updated__gt=timezone.now() - timedelta(seconds=20)))
                .order_by('date_created', 'id'))

    @property
    def revenue(self):
        return self.orders.revenue()

    @property
    def revenue_last_hour(self):
        return self.orders.last_hour().revenue()

    @property
    def order_count(self):
        return self.orders.count()


class Product(BaseModel):
    class Meta:
        ordering = ["date_created"]

    shops = models.ManyToManyField(Shop, related_name='products')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    picture = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=255, blank=True)
    
    price = models.BigIntegerField()

    @property
    def total_revenue(self):
        return self.line_items.exclude(order__status__in=['pending', 'error']).aggregate(Sum('total_amount')).get('total_amount__sum') or Decimal(0)

    @property
    def price_euro(self):
        return from_ap(self.price)

    @property
    def icon_url(self):
        url = 'https://app.abendpayments.com/static/organizer_backend/themes/default/icons/' + self.icon
        print('URL', url)
        return url


class OrderQuerySet(BaseQuerySet):
    def revenue(self):
        return self.paid().aggregate(Sum('total_amount')).get('total_amount__sum') or Decimal(0)

    def paid(self):
        return self.filter(status__in=['paid', 'ready', 'success'])

    def unfulfilled(self):
        return self.filter(status='paid')
    
    def oldest_first(self):
        return self.order_by('date_created')

    def ready(self):
        return self.filter(status='ready')

    def last_hour(self):
        end = timezone.now()
        start = end - timedelta(hours=1)
        return self.filter(date_created__range=[start, end])

    def blockchain_update_required(self):
        interval = timedelta(seconds=2)
        return self.filter(blockchain_checked_at__lt=timezone.now() - interval, status=Order.STATUS.pending)
        

def random_with_n_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def generate_pickup_code():
    return random_with_n_digits(4)
    #return get_random_string(length=4).upper()


class Order(BaseModel):
    class Meta:
        ordering = ["date_created"]

    serializer_class = 'OrderSerializer'        

    # has line_items
    shop = models.ForeignKey(Shop, models.DO_NOTHING, related_name='orders')
    user = models.ForeignKey(User, models.DO_NOTHING, related_name='orders')
    wallet = models.ForeignKey(Wallet, models.DO_NOTHING, related_name='orders')
    pickup_code = models.CharField(max_length=255, blank=True, default=generate_pickup_code)
    blockchain_checked_at = models.DateTimeField(null=True, blank=True)
    tx = models.CharField(max_length=255, blank=True)
    tx_hash = models.CharField(max_length=255, blank=True)

    class STATUS:
        pending = 'pending'
        paid = 'paid'
        ready = 'ready'
        success = 'success'
        error = 'error'

    STATUS_CHOICES = (
        (STATUS.pending, 'pending'),
        (STATUS.paid, 'paid'),
        (STATUS.ready, 'ready'),
        (STATUS.success, 'success'),
        (STATUS.error, 'error'),
    )

    status = models.CharField(max_length=255, choices=STATUS_CHOICES)
    total_amount = models.BigIntegerField()

    objects = OrderQuerySet.as_manager()

    def blockchain_tx(self):
        return blockchain.get_transfer_tx(self.wallet.pub_key, self.shop.pub_key, self.total_amount)

    def transmit_to_blockchain(self):
        try:
            self.tx = self.blockchain_tx()
            self.save()
            signed_tx = blockchain.sign(self.wallet.priv_key, self.tx)
            resp = blockchain.broadcast_signed_tx_sync(signed_tx)
            self.tx_hash = resp.get('tx_id')
            self.save()
            self.status = Order.STATUS.paid
            self.save()
        except:
            self.status = Order.STATUS.error
            self.save()

    def update_status_from_blockchain(self):
        if self.status != 'pending':
            return
        
        resp = blockchain.check_tx(self.tx_hash)

        self.blockchain_checked_at = timezone.now()
        self.save()
        
        if resp.get('status') == 'ok':
            self.status = Order.STATUS.paid
            self.save()
        


class LineItemQuerySet(BaseQuerySet):
    pass

class LineItem(BaseModel):
    class Meta:
        ordering = ["date_created"]

    @property
    def product_icon_url(self):
        return 'https://app.abendpayments.com/static/organizer_backend/themes/default/icons/' + self.product_icon

    product_ref = models.ForeignKey(Product, models.DO_NOTHING, related_name='line_items')
    product_price = models.BigIntegerField()
    product_icon = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    product_description = models.TextField(blank=True)
    product_picture = models.CharField(max_length=255, blank=True)

    order = models.ForeignKey(Order, models.CASCADE, related_name='line_items')

    count = models.IntegerField()
    total_amount = models.BigIntegerField()

    objects = LineItemQuerySet.as_manager()

    
