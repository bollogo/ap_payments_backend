from django.contrib.sites.models import Site
from django.conf import settings

def get_full_domain():
    site = Site.objects.get(id=settings.SITE_ID)
    https = True
    domain = site.domain
    if 'local' in site.domain or 'test' in site.domain:
        https = False
        
    success_url = '{}://{}'.format('https' if https else 'http', domain)
    return success_url

def to_ap(amount):
    return round(float(amount) * 1e8)

def from_ap(amount):
    if not amount:
        return 0
    return amount * 1e-8

