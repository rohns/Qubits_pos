from django.db import models
from sales.models import Sale

class Payment(models.Model):
    PAYMENT_METHODS = [('MPESA','M-PESA'),('CASH','Cash')]
    PAYMENT_STATUS = [('PENDING','Pending'),('PAID','Paid'),('FAILED','Failed'),('CANCELLED','Cancelled')]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    merchant_request_id = models.CharField(max_length=120, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=120, blank=True, null=True)
    result_code = models.CharField(max_length=20, blank=True, null=True)
    result_description = models.TextField(blank=True, null=True)
    mpesa_transaction_date = models.CharField(max_length=30, blank=True, null=True)
    raw_callback = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.method} Sale #{self.sale_id} {self.status}'
