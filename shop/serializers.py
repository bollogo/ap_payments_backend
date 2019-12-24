from rest_framework import routers, serializers, viewsets
from .models import Shop, LineItem, Order, Product
from users.serializers import WalletSerializer


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price',
            'icon', 'icon_url'
        )


class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = (
            'id', 'product_price', 'product_name',
            'product_description', 'product_icon',
            'product_icon_url',
            'count', 'total_amount'
        )


class ShopOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = (
            'id', 'name'
        )


class OrderSerializer(serializers.ModelSerializer):
    shop = ShopOrderSerializer(read_only=True)
    line_items = LineItemSerializer(read_only=True, many=True)
    tx = serializers.SerializerMethodField(method_name='get_tx')
    status_msg = serializers.SerializerMethodField(method_name='get_status_msg')
    wallet = WalletSerializer(read_only=True)

    def get_tx(self, obj):
        if hasattr(obj, 'tx'):
            return obj.tx
        return None

    def get_status_msg(self, obj):
        if obj.status == Order.STATUS.ready:
            return 'Your order is ready for pick up!!!'

        if obj.status == Order.STATUS.pending:
            return 'Processing payment...'
        
        if obj.status == Order.STATUS.paid:
            return 'Your order is being prepared...'

        if obj.status == Order.STATUS.success:
            return 'Enjoy your order'

    
    class Meta:
        model = Order
        fields = (
            'id', 'total_amount', 'status', 'date_created',
            'line_items', 'pickup_code',
            'shop', 'tx', 'status_msg', 'tx_hash', 'wallet'
        )


class ShopSerializer(serializers.ModelSerializer):
    recent_orders = OrderSerializer(read_only=True, many=True)
    orders_to_fulfill = OrderSerializer(read_only=True, many=True)
    products = ProductSerializer(read_only=True, many=True)

    class Meta:
        model = Shop
        fields = (
            'id', 'name', 'recent_orders', 'order_count', 'orders_to_fulfill',
            'revenue', 'revenue_last_hour', 'products', 'description'
        )


