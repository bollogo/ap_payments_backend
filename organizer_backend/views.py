from django.views.generic.edit import FormView, UpdateView, CreateView, DeleteView
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django import forms
from festival.models import Festival
from shop.models import Shop, Order
from users.models import Wallet, Payout, User
from .widgets import DatetimePickerWidget
from django.urls import reverse_lazy
from util.helper import to_ap, from_ap
from django.shortcuts import get_object_or_404


class HomeView(TemplateView):
    template_name = 'organizer_backend/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['festivals'] = self.request.user.festivals.all()
        return context

    
class FestivalDetailView(DetailView):
    template_name = 'organizer_backend/festival_detail.html'
    model = Festival


class FestivalDashboardView(DetailView):
    template_name = 'organizer_backend/festival_dashboard.html'
    model = Festival


class FestivalUsersView(ListView):
    template_name = 'organizer_backend/festival_users.html'
    model = User
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        festival = get_object_or_404(Festival, pk=self.kwargs.get('pk'))
        return festival.users().order_by('-date_created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['festival'] = get_object_or_404(Festival, pk=self.kwargs.get('pk'))
        return context


class FestivalEditView(DetailView):
    template_name = 'organizer_backend/festival_edit.html'
    model = Festival


class ShopFulfillmentView(DetailView):
    template_name = 'organizer_backend/shop_fulfillment.html'
    model = Shop


class ShopOrdersView(ListView):
    template_name = 'organizer_backend/shop_orders.html'
    model = Order
    context_object_name = 'orders'

    def get_queryset(self):
        shop = get_object_or_404(Shop, pk=self.kwargs.get('pk'))
        return shop.orders.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['shop'] = get_object_or_404(Shop, pk=self.kwargs.get('pk'))
        return context


class OrderRefreshView(DetailView):
    template_name = 'organizer_backend/order_refreshed.html'
    context_object_name = 'order'
    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        order = self.get_object()
        order.update_status_from_blockchain()
        context['order'] = order
        return context


class FestivalCreateForm(forms.ModelForm):
    class Meta:
        model = Festival
        fields = ['name', 'start_time']

        widgets= {
            'start_time': DatetimePickerWidget(),
        }
        

class FestivalCreateView(CreateView):
    template_name = 'organizer_backend/festival_create.html'
    form_class = FestivalCreateForm

    def form_valid(self, form):
        form.instance.owner = self.request.user

        self.object = form.instance

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('festival_edit', kwargs=dict(pk=self.object.pk))


class MintForm(forms.Form):
    pub_hash = forms.CharField()
    amount = forms.DecimalField()

    def clean_pub_hash(self):
        pub_hash = self.cleaned_data['pub_hash']
        try:
            wallet = Wallet.for_pub_hash(pub_hash)
        except Wallet.DoesNotExist:
            raise forms.ValidationError(
                'Wallet does not exist',
            )
        return pub_hash


class MintView(FormView):
    template_name = 'organizer_backend/mint.html'
    form_class = MintForm

    def get_success_url(self):
        return reverse_lazy('mint_success', kwargs={'pub_hash': self.pub_hash})

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        pub_hash = form.cleaned_data.get('pub_hash')

        wallet = Wallet.for_pub_hash(pub_hash)
        wallet.create_cash_charge(to_ap(amount))

        self.pub_hash = pub_hash
        
        return super().form_valid(form)


class MintSuccessView(TemplateView):
    template_name = 'organizer_backend/mint_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        pub_hash = self.kwargs.get('pub_hash')
        context['wallet'] = Wallet.for_pub_hash(pub_hash)

        return context


class PayoutForm(forms.Form):
    pub_hash = forms.CharField()

    def clean_pub_hash(self):
        pub_hash = self.cleaned_data['pub_hash']
        try:
            wallet = Wallet.for_pub_hash(pub_hash)
        except Wallet.DoesNotExist:
            raise forms.ValidationError(
                'Wallet does not exist',
            )
        return pub_hash

class PayoutView(FormView):
    template_name = 'organizer_backend/payout.html'
    form_class = PayoutForm

    def get_success_url(self):
        return reverse_lazy('payout_for_wallet', kwargs={'pub_hash': self.pub_hash})

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        pub_hash = form.cleaned_data.get('pub_hash')

        wallet = Wallet.for_pub_hash(pub_hash)
        self.pub_hash = pub_hash
        
        return super().form_valid(form)


class PayoutForWalletForm(forms.Form):
    amount = forms.DecimalField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs['min'] = 0.1


class PayoutForWalletView(FormView):
    template_name = 'organizer_backend/payout_for_wallet.html'
    form_class = PayoutForWalletForm

    def get_success_url(self):
        return reverse_lazy('payout_success', kwargs={'token': self.payout.token})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        pub_hash = self.kwargs.get('pub_hash')
        context['wallet'] = Wallet.for_pub_hash(pub_hash)

        return context

    def get_initial(self):
        pub_hash = self.kwargs.get('pub_hash')
        wallet = Wallet.for_pub_hash(pub_hash)
        return {'amount': from_ap(wallet.maximum_payout())}

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        pub_hash = self.kwargs.get('pub_hash')

        amount_ap = to_ap(amount)

        wallet = Wallet.for_pub_hash(pub_hash)
        self.pub_hash = pub_hash

        self.payout = wallet.create_payout(amount_ap)
        
        return super().form_valid(form)

    
class PayoutSuccessView(DetailView):
    slug_field = 'token'
    slug_url_kwarg = 'token'
    context_object_name = 'payout'
    
    template_name = 'organizer_backend/payout_success.html'
    model = Payout


