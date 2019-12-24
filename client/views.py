from django.views.generic.detail import DetailView
from django.views.generic import TemplateView
from shop.models import Shop
from festival.models import Festival


class FestivalView(DetailView):
    template_name = 'client/festival.html'
    model = Festival


class ShopView(DetailView):
    template_name = 'client/shop.html'
    model = Shop
    
