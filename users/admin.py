from django.contrib import admin
from .models import Voucher
from util.templatetags.util_filters import pretty_money

class VoucherAdmin(admin.ModelAdmin):
    fields = [
        'code',
        'date_created',
        'used_at',
        'amount',
        'charge',
    ]

    list_display = ['id', 'date_created', 'used_at', 'code', 'amount_pretty', 'charge']

    readonly_fields = ['date_created']

    def amount_pretty(self, obj):
        return pretty_money(obj.amount)
    
admin.site.register(Voucher, VoucherAdmin)
