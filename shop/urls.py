from django.urls import path
from .api import *
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

urlpatterns = [
    path(r'shops/', APIShopListView.as_view(), name='api_shop_list'),
    path(r'orders/create', api_order_create, name='api_order_create'),
    path(r'orders/<str:pub_hash>', APIOrderListView.as_view(), name='api_order_list'),
    path(r'charges/<str:pub_hash>', APIChargeListView.as_view(), name='api_charge_list'),
    path(r'orders/<uuid:pk>/sign', api_order_sign, name='api_order_sign'),
    path(r'shops/<uuid:id>/', APIShopDetailView.as_view(), name='api_shop_detail'),
    path(r'festivals/<uuid:pk_festival>/shops/update', api_festivals_shops_update, name='api_festivals_shops_update'),
    path(r'festivals/<uuid:pk>/dashboard', api_festivals_dashboard, name='api_festivals_dashboard'),
    path(r'shops/<uuid:pk>/fulfillment', api_shops_fulfillment, name='api_shops_fulfillment'),
    path(r'orders/<uuid:pk>/ready', api_order_set_ready, name='api_orders_set_ready'),
    path(r'orders/<uuid:pk>/success', api_order_set_success, name='api_orders_set_success'),
    path(r'paypal/<str:pub_hash>/pay', api_paypal_pay, name='api_paypal_pay'),
    path(r'voucher/<str:pub_hash>/submit', api_voucher_submit, name='api_voucher_submit'),
    path(r'wristbands/<str:token>', api_wristband_get, name='api_wristband_get'),
    path(r'wristbands/<str:token>/activate', api_wristband_activate, name='api_wristband_activate'),
    path(r'wristbands/<str:token>/charge', api_wristband_charge, name='api_wristband_charge'),
    path(r'wristbands/<str:token>/payout', api_wristband_payout, name='api_wristband_payout'),
    path(r'wristbands/<str:token>/spend', api_wristband_spend, name='api_wristband_spend'),
]
