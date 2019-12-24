from django.contrib import admin
from .models import Product, Shop, Order, LineItem

class ProductAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    list_display = ('id', 'name', 'description',)

admin.site.register(Product, ProductAdmin)


class ShopAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    list_display = ('id', 'name', 'description',)

admin.site.register(Shop, ShopAdmin)


class OrderAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    list_display = ('id', 'shop', 'total_amount', 'user')

admin.site.register(Order, OrderAdmin)
