"""cryptofest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, reverse_lazy
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

from transactions.views import *
from users.views import *
from shop.api import signup
from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token

urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('home'), permanent=False)),
    path('login/', auth_views.LoginView.as_view(template_name='organizer_backend/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='organizer_backend/logout.html'), name='logout'),
    
    path('admin/', admin.site.urls),

    # merchant
    path("create_invoice/", create_invoice),
    path("check_invoice/<uuid:id>/", check_invoice),

    # user
    path("broadcast_tx/", broadcast_tx),
    path("get_balance/<str:pub>/", get_balance),
    path("get_nonce/<str:pub>/", get_nonce),
    path("signup", signup),

    path('charges/<str:token>/success', ChargeSuccessView.as_view(), name='charge_success'),
    path('charges/<str:token>/details', ChargeDetailView.as_view(), name='charge_details'),
    path('charges/<str:token>/failure', ChargeCancelView.as_view(), name='charge_failure'),
    path('charges/<str:token>/cancel', ChargeCancelView.as_view(), name='charge_cancel'),

    url(r'^rest-auth/', include('rest_auth.urls')),

    # merchant admin
    path("stats/<str:merchant_key>/", StatsView.as_view()),

    path('api/', include('shop.urls')),

    path('organizer-backend/', include('organizer_backend.urls')),

    path('app/', include('client.urls')),
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-verify/', verify_jwt_token),
]
