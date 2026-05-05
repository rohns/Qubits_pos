from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','price','stock','is_service','active')
    search_fields = ('name',)
    list_filter = ('is_service','active')
