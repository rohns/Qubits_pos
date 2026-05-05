from django.db import models

CATEGORY_CHOICES = [
    ('PRINTING',    'Printing'),
    ('SCANNING',    'Scanning'),
    ('GOVERNMENT',  'Government Services'),
    ('INTERNET',    'Internet & Email'),
    ('FINANCIAL',   'Financial Services'),
    ('DOCUMENTS',   'Documents & Certificates'),
    ('PHONE',       'Phone Services'),
    ('OTHER',       'Other'),
]

class Product(models.Model):
    name       = models.CharField(max_length=120, unique=True)
    price      = models.DecimalField(max_digits=10, decimal_places=2)
    category   = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='OTHER', db_index=True)
    stock      = models.PositiveIntegerField(default=9999)
    is_service = models.BooleanField(default=True)
    active     = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
