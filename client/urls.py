from django.urls import path
from .views import *

urlpatterns = [
    path('festivals/<uuid:pk>', FestivalView.as_view(), name='client_festival_view'),
    path('shops/<uuid:pk>', ShopView.as_view(), name='client_shop_view'),
    path('orders/', ShopView.as_view(), name='client_orders_view'),
]

