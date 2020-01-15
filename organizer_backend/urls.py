from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

urlpatterns = [
    path(r'', login_required(HomeView.as_view()), name='home'),

    ###################
    #### Wristbands ####
    ###################
    path(r'wristbands/<uuid:pk>', login_required(WristbandDetailView.as_view()), name='wristband_detail'),

    ###################
    #### Festivals ####
    ###################
    path(r'festivals/<uuid:pk>', login_required(FestivalDetailView.as_view()), name='festival_detail'),
    path(r'festivals/<uuid:pk>/edit', login_required(FestivalEditView.as_view()), name='festival_edit'),
    path(r'festivals/<uuid:pk>/dashboard', login_required(FestivalDashboardView.as_view()), name='festival_dashboard'),
    path(r'festivals/<uuid:pk>/distribution', login_required(FestivalDistributionView.as_view()), name='festival_distribution'),
    path(r'festivals/<uuid:pk>/merchant_app', login_required(FestivalMerchantAppView.as_view()), name='festival_merchant_app'),
    path(r'orders/<uuid:pk>/refresh', login_required(OrderRefreshView.as_view()), name='orders_refresh'),
    path(r'festivals/<uuid:pk>/users', login_required(FestivalUsersView.as_view()), name='festival_users'),
    path(r'festivals/create', login_required(FestivalCreateView.as_view()), name='festival_create'),
    path(r'shops/<uuid:pk>/fulfillment', login_required(ShopFulfillmentView.as_view()), name='shop_fulfillment'),
    path(r'shops/<uuid:pk>/orders', login_required(ShopOrdersView.as_view()), name='shop_orders'),
    path(r'mint/', staff_member_required(login_required(MintView.as_view())), name='mint'),
    path(r'mint/<str:pub_hash>/success', staff_member_required(login_required(MintSuccessView.as_view())), name='mint_success'),
    path(r'payout/', staff_member_required(login_required(PayoutView.as_view())), name='payout'),
    path(r'payout_for_wallet/<str:pub_hash>', staff_member_required(login_required(PayoutForWalletView.as_view())), name='payout_for_wallet'),
    path(r'payout/<str:token>/success', staff_member_required(login_required(PayoutSuccessView.as_view())), name='payout_success'),
]
