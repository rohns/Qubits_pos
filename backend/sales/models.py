import random, string
from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from django.utils import timezone

def generate_receipt_number():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits  = ''.join(random.choices(string.digits, k=5))
    return f"QBS-{letters}{digits}"

class Sale(models.Model):
    STATUS_CHOICES  = [('PENDING','Pending'),('PAID','Paid'),('FAILED','Failed'),('CANCELLED','Cancelled')]
    PAYMENT_CHOICES = [('NONE','None'),('CASH','Cash'),('MPESA','M-PESA'),('CREDIT','Credit / Tab')]

    receipt_number = models.CharField(max_length=20, unique=True, blank=True, db_index=True)
    cashier        = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    total_amount   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='NONE')
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    # Who owes for this sale. Only required for CREDIT sales, but kept generally
    # available since it's also useful on cash/M-PESA receipts.
    customer_name  = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    created_at     = models.DateTimeField(db_index=True)  # Allow manual dates
    sale_date      = models.DateField(blank=True, null=True, db_index=True)  # Extracted date for reports

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            for _ in range(10):
                rn = generate_receipt_number()
                if not Sale.objects.filter(receipt_number=rn).exists():
                    self.receipt_number = rn
                    break
        # Extract date for easier reporting
        if self.created_at:
            self.sale_date = self.created_at.date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Sale {self.receipt_number} - {self.status}'

class SaleItem(models.Model):
    sale       = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product    = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity   = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
