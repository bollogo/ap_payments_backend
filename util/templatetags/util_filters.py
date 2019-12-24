from django import template
from django.utils.safestring import mark_safe
import json
from django.core import serializers
from django.db.models.query import QuerySet
from rest_framework.renderers import JSONRenderer
from decimal import Decimal
from util.helper import to_ap, from_ap
import pytz
tz = pytz.timezone('Europe/Vienna')
from datetime import datetime, date, timedelta, timezone

register = template.Library()

@register.filter
def jsonify(value):
    if isinstance(value, QuerySet):
        if hasattr(value, 'to_dict'):
            return mark_safe(JSONRenderer().render(value.to_dict()).decode("utf-8"))
        return mark_safe(serializers.serialize('json', value))

    return mark_safe(JSONRenderer().render((value)).decode("utf-8"))


@register.filter(name='pretty_money')
def pretty_money(value, arg=',', currency='€'):
    value = from_ap(value)
    if value is None:
        return '-'

    if isinstance(value, int):
        return ('{:,.2f} {}'.format(value/100.0, currency).replace(',', '"').replace('.', arg).replace('"', '.'))
    elif isinstance(value, (Decimal, float)):
        return '{:,.2f} {}'.format(value, currency).replace(',', '"').replace('.', arg).replace('"', '.')

    return '{:,.2f} {}'.format(value, currency).replace(',', '"').replace('.', arg).replace('"', '.')


@register.filter
def rg_date(val):
    if isinstance(val, datetime):
        return val.astimezone(tz).strftime('%d.%m.%Y')
    if isinstance(val, date):
        return val.strftime('%d.%m.%Y')

    return '-'


@register.filter
def rg_date_and_time(val, verbose=False):
    if not verbose:
        if isinstance(val, datetime):
            return val.astimezone(tz).strftime('%a, %d.%m.%Y %H:%M Uhr')
        if isinstance(val, date):
            return val.strftime('%a, %d.%m.%Y %H:%M Uhr')
    else:
        if isinstance(val, datetime):
            return val.astimezone(tz).strftime('%a, %d.%m.%Y %H:%M Uhr')
        if isinstance(val, date):
            return val.strftime('%a, %d.%m.%Y %H:%M Uhr')

    return '-'


@register.filter
def rg_time(val):
    if isinstance(val, datetime):
        return val.astimezone(tz).strftime('%H:%M Uhr')
    if isinstance(val, date):
        return val.strftime('%H:%M Uhr')

    return '-'

