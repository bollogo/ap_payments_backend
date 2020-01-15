from django.views.generic.detail import DetailView
from users.models import Wristband


class WristbandDetailView(DetailView):
    template_name = 'organizer_backend/wristband_detail.html'
    model = Wristband


