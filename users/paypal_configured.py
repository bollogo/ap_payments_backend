import paypalrestsdk
from django.conf import settings

paypalrestsdk.configure({
    'mode': settings.PAYPAL_MODE,
    'openid_client_id': settings.PAYPAL_CLIENT_ID,
    'openid_client_secret': settings.PAYPAL_CLIENT_SECRET,
    'client_id': settings.PAYPAL_CLIENT_ID,
    'client_secret': settings.PAYPAL_CLIENT_SECRET,
})

paypal_commission_email = settings.PAYPAL_COMMISSION_EMAIL
