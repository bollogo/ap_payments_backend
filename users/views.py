from django.views.generic.detail import DetailView
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from users.models import Charge
from django.shortcuts import redirect
from django.http import Http404, HttpResponse


class ChargeCancelView(DetailView):
    slug_field = 'token'
    slug_url_kwarg = 'token'
    context_object_name = 'charge'
    template_name = 'users/charge_cancel.html'
    model = Charge


class ChargeFailureView(DetailView):
    slug_field = 'token'
    slug_url_kwarg = 'token'
    context_object_name = 'charge'
    template_name = 'users/charge_failure.html'
    model = Charge


class ChargeDetailView(DetailView):
    slug_field = 'token'
    slug_url_kwarg = 'token'
    context_object_name = 'charge'
    template_name = 'users/charge_details.html'
    model = Charge

    def get(self, request, *args, **kwargs):
        try:
            # Basically go to failure view in case something is not right.
            token = self.kwargs.get('token')
            charge = get_object_or_404(Charge, token=token)
            
            if not charge.is_paid:
                raise Http404

        except Http404:
            return redirect(reverse_lazy('charge_failure', kwargs={'token': token}))

        return super().get(request, *args, **kwargs)


class ChargeSuccessView(RedirectView):
    def get_redirect_url(self, **kwargs):
        charge = get_object_or_404(Charge, token=kwargs.get('token'))

        success_url = reverse_lazy('charge_details', kwargs={'token': charge.token})
        if charge.is_paid:
            return success_url

        # We first have to finish this purpose, if it is not successful, we have to think of something else
        try:
            charge.finish()
        except:
            return reverse_lazy('charge_failure',
                                kwargs={'token': self.kwargs.get('token')})

        return success_url
