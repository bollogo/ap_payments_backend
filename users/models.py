import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import Q, F, Count, Sum, Exists, ExpressionWrapper, Case, When, Min
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from transactions import blockchain
from transactions.blockchain import response_ok
from util.helper import to_ap, from_ap, get_full_domain
from django.urls import reverse_lazy
from .paypal_configured import paypalrestsdk
import hashlib
from .paypal import paypal_create_payment
from django.utils.crypto import get_random_string
from decimal import Decimal
from .exceptions import InvalidVoucherException, NotEnoughFunds
from util.models import BaseModel, BaseQuerySet
import django_rq

class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("ENTER AN EMAIL BUDDY")
        
        user = self.model(email=self.normalize_email(email))
        
        if password:
            user.set_password(password)
        
        user.save()
        return user
    
    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), blank=True, unique=True)
    app_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    # Needed as a fake for rest-auth
    @property
    def username(self):
        return self.email

    @property
    def wallet(self):
        return self.wallets.first()


class WalletQuerySet(BaseQuerySet):
    def balance(self):
        return self.aggregate(Sum('balance')).get('balance__sum') or int(0)


class Wallet(BaseModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    pub_key = models.CharField(max_length=255)
    priv_key = models.CharField(max_length=255, null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, models.CASCADE, related_name='wallets')
    balance = models.BigIntegerField()

    objects = WalletQuerySet.as_manager()

    @classmethod
    def create(cls, user, balance=0, precharge=True):
        priv_key, pub_key = blockchain.create_wallet()
        wallet = Wallet.objects.create(
            pub_key=pub_key,
            priv_key=priv_key,
            balance=balance,
            user=user,
        )
        if precharge:
            django_rq.enqueue(wallet.precharge_with_aeter)
        return wallet

    def precharge_with_aeter(self):
        return blockchain.transfer_aeter(self.pub_key)

    @classmethod
    def for_pub_key(cls, pub_key):
        return cls.objects.get(pub_key=pub_key)

    @classmethod
    def for_pub_hash(cls, pub_hash):
        return cls.objects.get(pub_key__endswith=pub_hash)

    @property
    def wristband(self):
        return self.wristbands.first()

    @property
    def pub_hash(self):
        return self.pub_key[-6:]

    @property
    def balance_euro(cls):
        return from_ap(self.balance)

    def ae_explorer_url(self):
        return 'https://testnet.explorer.aepps.com/#/account/{}'.format(self.pub_key)

    def sign_tx(self, pub_key, data):
        return blockcahain.create_signed_tx(self.priv_key, self.pub_key, amount, pub_key)

    def charge(self, amount_ap):
        self.balance += amount_ap
        self.save()

    def balance_from_blockchain(self):
        return blockchain.get_balance(self.pub_key)

    def create_cash_charge(self, amount_ap):
        charge = Charge.objects.create(
            amount=amount_ap,
            payment_method=Charge.PAYMENT_METHOD.generated,
            wallet=self,
            is_paid=True
        )

        django_rq.enqueue(charge.transmit_to_blockchain)
        self.charge(amount_ap)
        return charge

    def create_order_and_spend(self, order_id, shop, total_amount):
        from shop.models import Order
        order = Order.objects.create(
            id=order_id,
            shop=shop,
            user=self.user,
            wallet=self,
            status=Order.STATUS.pending,
            total_amount=total_amount,
        )

        django_rq.enqueue(order.transmit_to_blockchain)
        self.spend(total_amount)
        return order

    def sum_charges_paypal(self):
        return self.charges.filter(is_paid=True, payment_method=Charge.PAYMENT_METHOD.paypal).aggregate(Sum('amount')).get('amount__sum') or int(0)

    def sum_charges_cash(self):
        return self.charges.filter(is_paid=True, payment_method=Charge.PAYMENT_METHOD.generated).aggregate(Sum('amount')).get('amount__sum') or int(0)

    def sum_orders_paid(self):
        return self.orders.exlude(status='pending').aggregate(Sum('total_amount')).get('total_amount__sum') or int(0)

    def burn(self, amount_ap):
        self.balance -= amount_ap
        self.save()

    def spend(self, amount_ap):
        if self.balance < amount_ap:
            raise NotEnoughFunds('Trying to spend {} but balance is {}', self.balance, amount_ap)
        self.balance -= amount_ap
        self.save()

    def transfer_aeter(self, amount):
        return blockchain.transfer_aeter(self.pub_key, amount)

    def update_balance_from_blockchain(self):
        return self.balance
        new_balance = blockchain.get_balance(self.pub_key)
        if new_balance is not None:
            self.balance = new_balance
            self.save()

        return self.balance

    def maximum_payout(self):
        first_charge = to_ap(2)
        spent = self.orders.all().aggregate(Sum('total_amount')).get('total_amount__sum') or int(0)

        subtract = max(0, first_charge - spent)

        return int(self.balance - subtract)

    def create_payout(self, amount_ap):
        amount_ap = min(self.maximum_payout(), amount_ap)
        
        payout = Payout.objects.create(wallet=self, amount=amount_ap)
        django_rq.enqueue(payout.transmit_to_blockchain)
        
        self.balance -= amount_ap
        self.save()
        return payout
        

def generate_token():
    token = get_random_string(length=20) + '-ksa)§öü9403oplwefdkbgmdslpergkjalksjdäaslkdjlsadjhnbvm'
    return str(hashlib.sha1(token.encode('utf8')).hexdigest())

def generate_code():
    return get_random_string(length=4)


class PayoutQuerySet(BaseQuerySet):
    def total_amount(self):
        return self.aggregate(models.Sum('amount')).get('amount__sum') or Decimal(0)


class Payout(BaseModel):
    serializer_class = 'PayoutSerializer'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(unique=True, max_length=512, default=generate_token)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    wallet = models.ForeignKey(Wallet, models.CASCADE, related_name='payouts')

    amount = models.BigIntegerField()
    
    # TODO: think if these status choices make sense
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

    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default=STATUS.pending)
    

    objects = PayoutQuerySet.as_manager()
    
    def transmit_to_blockchain(self):
        try:
            resp = blockchain.burn(self.wallet.pub_key, self.amount)
            if response_ok(resp):
                self.status = Charge.STATUS.success
            else:
                self.status = Charge.STATUS.error
            self.save()
            
            return resp
        except Exceptions as err:
            print(err)
            self.status = Charge.STATUS.error
            self.save()


    @property
    def amount_euro(self):
        return from_ap(self.amount)


class VoucherQuerySet(BaseQuerySet):
    def unused(self):
        return self.filter(Q(valid_until__isnull=True, charge__isnull=True) |
                           Q(valid_until__isnull=True, valid_until__lt=timezone.now(), charge__isnull=True))


class Voucher(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(unique=True, max_length=512, default=generate_code)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    used_at = models.DateTimeField(null=True, blank=True)

    valid_until = models.DateTimeField(null=True, blank=True)
    charge = models.ForeignKey('Charge', models.CASCADE, related_name='voucher', null=True, blank=True)
    
    amount = models.BigIntegerField()

    objects = VoucherQuerySet.as_manager()

    def unused(self):
        return Voucher.objects.filter(pk=self.pk).unused().exists()

    def use_with_charge(self, charge):
        self.used_at = timezone.now()
        self.charge = charge
        self.save()


class ChargeQuerySet(BaseQuerySet):
    def paypal(self):
        return self.filter(payment_method=Charge.PAYMENT_METHOD.paypal)
    
    def cash(self):
        return self.filter(payment_method=Charge.PAYMENT_METHOD.generated)

    def paid(self):
        return self.filter(is_paid=True)
        
    def total_amount(self):
        return self.aggregate(models.Sum('amount')).get('amount__sum') or Decimal(0)


class Charge(BaseModel):
    serializer_class = 'ChargeSerializer'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(unique=True, max_length=512, default=generate_token)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    amount = models.BigIntegerField()
    is_paid = models.BooleanField(default=False)
    wallet = models.ForeignKey(Wallet, models.CASCADE, related_name='charges')
    
    paypal_payment_id = models.CharField(max_length=255, blank=True, null=True)
    fees_paypal = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    paypal_buyer_email = models.CharField(max_length=255, blank=True, null=True)
    paypal_transaction_id_organizer = models.CharField(max_length=255, blank=True, null=True)
    paypal_approval_url = models.CharField(max_length=1500, blank=True, null=True)

    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_source_id = models.CharField(max_length=1000, blank=True, null=True)
    fees_stripe = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, default=0)

    class PAYMENT_METHOD:
        paypal = 'paypal'
        stripe_creditcard = 'stripe_creditcard'
        stripe_sofort = 'stripe_sofort'
        stripe_giropay = 'stripe_giropay'
        invoice = 'invoice'
        rausweis = 'rausweis'
        generated = 'generated'
        cash = 'cash'
        voucher = 'voucher'

    PAYMENT_METHOD_CHOICES = (
        (PAYMENT_METHOD.paypal, 'paypal'),
        (PAYMENT_METHOD.stripe_creditcard, 'stripe_creditcard'),
        (PAYMENT_METHOD.stripe_sofort, 'stripe_sofort'),
        (PAYMENT_METHOD.stripe_giropay, 'stripe_giropay'),
        (PAYMENT_METHOD.invoice, 'invoice'),
        (PAYMENT_METHOD.rausweis, 'rausweis'),
        (PAYMENT_METHOD.generated, 'generated')
    )
    
    payment_method = models.CharField(choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD.paypal, max_length=100)

    # TODO: think if these status choices make sense
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

    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default=STATUS.pending)

    objects = ChargeQuerySet.as_manager()

    def transmit_to_blockchain(self):
        try:
            resp = blockchain.mint(self.wallet.pub_key, self.amount)
            if response_ok(resp):
                self.status = Charge.STATUS.success
            else:
                self.status = Charge.STATUS.error
            self.save()
            return resp
        except Exception as err:
            print(err)
            self.status = Charge.STATUS.error
            self.save()

    @property
    def amount_euro(self):
        return from_ap(self.amount)

    def generate_success_url(self):
        return get_full_domain() + str(reverse_lazy('charge_success', kwargs={'token': self.token}))

    def generate_cancel_url(self):
        return get_full_domain() + str(reverse_lazy('charge_cancel', kwargs={'token': self.token}))

    def set_paid_and_transfer(self):
        # Need to lock this.
        if self.is_paid:
            return

        self.is_paid = True

        self.wallet.charge(self.amount)
        self.save()

    @classmethod
    def create_with_paypal(cls, wallet, amount):
        charge = cls.objects.create(
            wallet=wallet,
            amount=amount,
            payment_method=Charge.PAYMENT_METHOD.paypal
        )

        charge.fees_paypal = 0

        payment = paypal_create_payment(charge)

        charge.paypal_payment_id = payment.id

        charge.save()

        # TODO: What if getting the approval url does not work? Well we have to throw an error anyways.
        charge.paypal_approval_url = [link for link in payment.links if link.rel == 'approval_url'][0].href
        charge.save()

        return charge

    @classmethod
    def create_with_voucher(cls, wallet, code):
        voucher = Voucher.objects.filter(code__iexact=code).unused().first()
        if not voucher:
            raise InvalidVoucherException()
        
        charge = cls.objects.create(
            wallet=wallet,
            amount=voucher.amount,
            payment_method=Charge.PAYMENT_METHOD.voucher
        )

        voucher.use_with_charge(charge)
        voucher.save()
        
        charge.set_paid_and_transfer()

        return charge
        
    def finish_paypal(self):
        payment = paypalrestsdk.Payment.find(self.paypal_payment_id)
        payer_id = payment.payer.payer_info.payer_id

        if payment.execute({"payer_id": payer_id}):
            print("Payment execute successfully")
        else:
            print(payment.error) # Error Hash

        sale = payment.transactions[0].related_resources[0].sale
        if payment.state == 'approved' and sale.state == 'completed':
            self.set_paid_and_transfer()

        if not self.is_paid:
            self.save()
            return

        try:
            self.fees_paypal = Decimal(sale.transaction_fee.value)
        except:
            pass

        self.save()

        self.paypal_buyer_email = payment.payer.email
        self.paypal_transaction_id = sale.id

        self.save()

    def finish(self):
        if self.is_paid:
            return

        #with transaction.atomic(using='wunderfest'): # implement this later, when we use postgres.
        if self.payment_method == 'paypal':
            return self.finish_paypal()


class Wristband(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(unique=True, max_length=512)

    wallet = models.ForeignKey(Wallet, models.CASCADE, related_name='wristbands')

    class STATUS:
        active = 'ACTIVE'
        disabled = 'DISABLED'

    STATUS_CHOICES = (
        (STATUS.active, 'ACTIVE'),
        (STATUS.disabled, 'DISABLED'),
    )

    status = models.CharField(max_length=255, choices=STATUS_CHOICES)

