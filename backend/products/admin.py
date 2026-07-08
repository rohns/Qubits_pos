from django.contrib import admin
from .models import Product, StockMovement

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'track_stock', 'reorder_level', 'is_low_stock', 'is_service', 'active')
    search_fields = ('name',)
    list_filter = ('category', 'track_stock', 'is_service', 'active')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_change', 'reason', 'recorded_by', 'created_at')
    list_filter = ('reason',)
    search_fields = ('product__name', 'note')
    autocomplete_fields = ('product',)
