from django.db import models
from django.contrib.auth.models import User

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('RENT','Rent'),('INTERNET','Internet'),('ELECTRICITY','Electricity'),
        ('PAPER','Printing Paper'),('TONER','Toner/Ink'),('WAGES','Employee Wages'),
        ('TRANSPORT','Transport'),('MAINTENANCE','Maintenance'),('OTHER','Other'),
    ]
    PAYMENT_METHODS = [('CASH','Cash'),('MPESA','M-PESA'),('BANK','Bank'),('OTHER','Other')]

    recorded_by    = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    date           = models.DateField(db_index=True)
    category       = models.CharField(max_length=30, choices=CATEGORY_CHOICES, db_index=True)
    description    = models.CharField(max_length=255)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    created_at     = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f'{self.category} - {self.amount}'
