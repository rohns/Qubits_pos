from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id','sale','method','status','amount','amount_paid','change_due','phone_number','mpesa_receipt_number','mpesa_reference','created_at','updated_at')
    search_fields = ('mpesa_receipt_number','mpesa_reference','phone_number','checkout_request_id','merchant_request_id')
    list_filter = ('method','status','created_at')
