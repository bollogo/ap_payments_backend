from .paypal_configured import paypalrestsdk, paypal_commission_email
import urllib
import re

def encodeURIComponent(s):
    return urllib.parse.quote(s.encode("utf-8"))

def paypal_create_payment(charge):
    shortDescription = '{} € Aufladung für Geheimkonzert '.format(
        charge.amount_euro,
    )

    items = [{
        'name': 'Aufladung {} €'.format(charge.amount_euro),
        "sku": 'C' + charge.wallet.pub_hash,
        "price": '{:.2f}'.format(charge.amount_euro),
        "currency": 'EUR',
        "quantity": 1
    }]
    
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": charge.generate_success_url(),
            "cancel_url": charge.generate_cancel_url()
        },
        "transactions": [{
            "item_list": {
                    "items": items
            },
            "amount": {
                "total": '{:.2f}'.format(charge.amount_euro),
                "currency": "EUR"
            },
            "description": shortDescription}]
    })

    if payment.create():
        return payment

    raise Exception(payment.error)
