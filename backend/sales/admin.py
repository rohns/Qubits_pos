from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('product','quantity','unit_price','line_total')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id','cashier','customer_name','total_amount','status','payment_method','created_at')
    list_filter = ('status','payment_method')
    search_fields = ('receipt_number','customer_name','customer_phone')
    inlines = [SaleItemInline]
