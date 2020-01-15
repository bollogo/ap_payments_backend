from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from rest_framework import routers, serializers, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from shop.models import Shop, Product, Order, LineItem
from users.models import User, Wallet, Charge, Voucher, Wristband
from festival.models import Festival
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from transactions import blockchain
from transactions.blockchain import response_ok
from util.helper import from_ap, to_ap
from decimal import Decimal
from users.exceptions import InvalidVoucherException, NotEnoughFunds
from .serializers import LineItemSerializer, ProductSerializer, ShopSerializer, OrderSerializer
from festival.serializers import FestivalSerializer
from users.serializers import ChargeSerializer
from django.utils import timezone
from django.utils.crypto import get_random_string
from util.helper import to_ap, from_ap, get_full_domain
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class APIShopListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopSerializer

    def get_queryset(self):
        festival = Festival.objects.get(name='Aeternity Universe One')
        return festival.shops.all()


class APIFestivalListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FestivalSerializer

    def get_queryset(self):
        return self.request.user.festivals.all()


class APIFestivalShopListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopSerializer

    def get_queryset(self):
        festival = Festival.objects.get(pk=self.kwargs['pk'])
        return festival.shops.all()


class APIShopDetailView(RetrieveAPIView):
    #    permission_classes = (IsAuthenticated,)
    serializer_class = ShopSerializer

    def get_queryset(self):
        return Shop.objects.all()


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def api_festivals_shops_update(request, pk_festival):
    # Only allow the owner to edit a festival for now.
    festival = get_object_or_404(Festival, pk=pk_festival, owner=request.user)

    shops_data = request.data
    shop_ids = []

    for shop_data in shops_data:
        shop, shop_created = Shop.update_or_create(
            id=shop_data.get('id'),
            owner=request.user,
            festival=festival,
            defaults=dict(
                name=shop_data.get('name')
            )
        )
        shop_ids.append(shop.id)

        product_ids = []
        for product_data in shop_data.get('products', []):
            product, product_created = Product.objects.update_or_create(
                id=product_data.get('id'),
                defaults=dict(
                    name=product_data.get('name'),
                    price=to_ap(product_data.get('price')),
                    icon=product_data.get('icon') or '',
                )
            )
            product.shops.add(shop)
            product_ids.append(product.id)

        # Delete all products, which were not transferred
        shop.products.exclude(id__in=product_ids).delete()

    # Delete all shops, which were not transferred
    festival.shops.exclude(id__in=shop_ids).delete()

    return Response({'msg': 'OK'})


class APIOrderListView(ListAPIView):
    #    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer

    def get_queryset(self):
        wallet = Wallet.for_pub_hash(self.kwargs.get('pub_hash'))
        user = wallet.user
        orders = user.orders.order_by('-date_created', 'id')
        for order in orders.blockchain_update_required():
            order.update_status_from_blockchain()
            
        return orders


class APIChargeListView(ListAPIView):
    #    permission_classes = (IsAuthenticated,),
    serializer_class = ChargeSerializer

    def get_queryset(self):
        wallet = Wallet.for_pub_hash(self.kwargs.get('pub_hash'))
        return wallet.charges.all().order_by('-date_created', 'id')

def serialize_payout(payout):
    return dict(
        id=payout.id,
        amount=payout.amount,
        date_created=payout.date_created
    )

def serialize_charge(charge):
    return dict(
        id=charge.id,
        amount=charge.amount,
        date_created=charge.date_created,
        payment_method=charge.payment_method,
        is_paid=charge.is_paid
    )

def serialize_order(order):
    return order.to_dict()

def serialize_wristband(wristband):
    wallet_dict = None
    wallet = wristband.wallet
    if wallet:
        wallet_dict = {
            'id': wallet.id,
            'balance': wallet.balance,
            'maximum_payout': wallet.maximum_payout(),
            'charges': [serialize_charge(charge) for charge in wallet.charges.all()],
            'orders': [serialize_order(order) for order in wallet.orders.paid()],
            'payouts': [serialize_payout(payout) for payout in wallet.payouts.all()],
        }
        
    return {
        'id': wristband.id,
        'token': wristband.token,
        'status': wristband.status,
        'wallet': wallet_dict
    }

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_wristband_charge(request, token):
    try:
        amount = request.data.get('amount')
        wristband = Wristband.objects.get(token=token)

        wristband.wallet.create_cash_charge(amount)
        
        return Response(serialize_wristband(wristband))

    except Wristband.DoesNotExist as e:
        print(e)
        return Response({'err': 'wristband_not_registered', 'status': 'NOT_REGISTERED'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_wristband_payout(request, token):
    try:
        amount = request.data.get('amount')
        wristband = Wristband.objects.get(token=token)

        payout = wristband.wallet.create_payout(amount)
        
        return Response(serialize_wristband(wristband))

    except Wristband.DoesNotExist as e:
        print(e)
        return Response({'err': 'wristband_not_registered', 'status': 'NOT_REGISTERED'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_wristband_spend(request, token):
    try:
        amount = request.data.get('amount')
        shop_id = request.data.get('shop_id')
        # Optionally, provide a order id, if it was created inside the app.
        order_id = request.data.get('order_id', None)
        wristband = Wristband.objects.get(token=token)
        wallet = wristband.wallet

        shop = Shop.objects.get(pk=shop_id)
        order = wristband.wallet.create_order_and_spend(
            order_id,
            shop=shop,
            total_amount=amount,
        )

        return Response(serialize_wristband(wristband))

    except Wristband.DoesNotExist as e:
        return Response({'err': 'wristband_not_registered', 'token': token, 'status': 'NOT_REGISTERED'}, 400)

    except NotEnoughFunds as e:
        order.status = Order.STATUS.error
        return Response({'err': 'Not enough funds', 'token': token, 'status': 'NOT_REGISTERED'}, 400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_wristband_get(request, token):
    try:
        wristband = Wristband.objects.get(token=token)
        return Response(serialize_wristband(wristband))
    
    except Wristband.DoesNotExist as e:
        print(e)
        return Response({'err': 'wristband_not_registered', 'token': token, 'status': 'NOT_REGISTERED'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_wristband_activate(request, token):
    wristband = Wristband.objects.filter(token=token).first()
    if wristband:
        return Response({'err': 'wristband already activated'})

    user = User.objects.create(
        email='wristband_{}@cryptofest.net'.format(token)
    )

    wallet = Wallet.create(user)
    
    wristband = Wristband.objects.create(
        token=token,
        wallet=wallet,
        status=Wristband.STATUS.active,
    )

    return Response(serialize_wristband(wristband))


@api_view(['POST'])
#@permission_classes((IsAuthenticated,))
def api_order_sign(request, pk):
    order = get_object_or_404(Order, pk=pk)
    signed_tx = request.data.get('signed_tx')

    resp = blockchain.broadcast_signed_tx(signed_tx)
    order.tx_hash = resp.get('tx_id')
    order.save()
    
    if response_ok(resp):
        order.status = Order.STATUS.paid

    order.blockchain_checked_at = timezone.now()

    order.wallet.spend(order.total_amount)

    order.save()

    wallet = order.wallet
    wallet.update_balance_from_blockchain()
    
    return Response(OrderSerializer(order).data)

@api_view(['POST'])
#@permission_classes((IsAuthenticated,))
def api_paypal_pay(request, pub_hash):
    wallet = Wallet.for_pub_hash(pub_hash)
    amount = to_ap(Decimal(request.data.get('amount')))

    # Generate Paypal URL
    charge = Charge.create_with_paypal(wallet, amount)

    return Response({'url': charge.paypal_approval_url})


@api_view(['POST'])
#@permission_classes((IsAuthenticated,))
def api_voucher_submit(request, pub_hash):
    wallet = Wallet.for_pub_hash(pub_hash)
    code = request.data.get('code')

    print('CODE', code)

    try:
        charge = Charge.create_with_voucher(wallet, code)
    except InvalidVoucherException as e:
        resp = Response({'msg': 'Voucher not found.'}, status=status.HTTP_404_NOT_FOUND)
        return resp
    
    return Response({'id': charge.id, 'amount': charge.amount})

    
@api_view(['POST'])
#@permission_classes((IsAuthenticated,))
def api_order_create(request):
    items = request.data.get('items')
    shop_data = request.data.get('shop')
    shop = get_object_or_404(Shop, pk=shop_data.get('id'))
    user_pubkey = request.data.get('pubkey')

    wallet = Wallet.for_pub_key(user_pubkey)
    user = wallet.user

    # TODO Make transaction out of this entire function.
    order = Order.objects.create(
        shop=shop,
        user=user,
        wallet=wallet,
        status=Order.STATUS.pending,
        total_amount=0,
    )

    total_amount = 0
        
    for item in items:
        product_id = item.get('id')
        count = item.get('count')

        if not count:
            continue
        
        product = Product.objects.get(pk=product_id, shops__in=[shop])

        amount = count * product.price
        line_item = LineItem(
            product_ref=product,
            product_price=product.price,
            product_name=product.name,
            product_description=product.description,
            product_picture=product.picture,
            product_icon=product.icon,
            order=order,
            count=count,
            total_amount=amount,
        )

        line_item.save()
        total_amount += product.price * count

    order.total_amount = total_amount
    order.save()

    order.tx = blockchain.get_transfer_tx(wallet.pub_key, shop.pub_key, total_amount)

    return Response(OrderSerializer(order).data)
    # TODO: Assure price is similar to client price or FAIL

@api_view(['POST'])
def signup(request):
    pub_key = request.data.get('pub_key')

    try:
        wallet = Wallet.for_pub_key(pub_key)
    except Wallet.DoesNotExist:
        pub_hash = pub_key[-6:]
        user = User.objects.create(
            email='{}@cryptofest.net'.format(pub_hash)
        )
        
        wallet = Wallet.objects.create(
            pub_key=pub_key,
            balance=0,
            user=user,
        )

        wallet.transfer_aeter(int(0.01 * 10e18))

    return Response(dict(
        id=wallet.user.id,
    ))


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def api_festivals_dashboard(request, pk):
    festival = get_object_or_404(Festival, pk=pk)

    return Response({'shops': festival.shops.to_dict()})


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def api_shops_fulfillment(request, pk):
    shop = get_object_or_404(Shop, pk=pk)

    return Response({
        'ready_order_count': shop.ready_order_count,
        'unfulfilled_order_count': shop.unfulfilled_order_count,
        'orders': shop.orders_to_fulfill.to_dict()})


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def api_order_set_ready(request, pk):
    order = get_object_or_404(Order, pk=pk)

    order.status = Order.STATUS.ready
    order.save()

    return Response(order.to_dict())
    

@api_view(['POST'])
#@permission_classes((IsAuthenticated,))
def api_order_set_success(request, pk):
    order = get_object_or_404(Order, pk=pk)

    order.status = Order.STATUS.success
    order.save()

    return Response(order.to_dict())
