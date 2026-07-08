from django.db import models
from django.contrib.auth.models import User

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
    name          = models.CharField(max_length=120, unique=True)
    price         = models.DecimalField(max_digits=10, decimal_places=2)
    category      = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='OTHER', db_index=True)
    stock         = models.PositiveIntegerField(default=9999)
    is_service    = models.BooleanField(default=True)
    active        = models.BooleanField(default=True, db_index=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    # --- Inventory tracking ---
    # Pure services (e.g. "Browsing per minute") never run out, so stock tracking
    # is opt-in. Turn this on for consumables like paper reams, toner cartridges, etc.
    track_stock   = models.BooleanField(
        default=False,
        help_text="If enabled, stock decrements on each sale and low-stock alerts apply."
    )
    reorder_level = models.PositiveIntegerField(
        default=0,
        help_text="When stock falls to or below this number, the item shows up as low-stock."
    )

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.track_stock and self.stock <= self.reorder_level

    def adjust_stock(self, delta, reason, user=None, note=""):
        """
        Adjust stock by delta (positive = restock/adjustment up, negative = consumption)
        and record it as a StockMovement. Only meaningful when track_stock is True,
        but works regardless so restocking can be logged before tracking is switched on.
        """
        self.stock = max(0, self.stock + delta)
        self.save(update_fields=['stock'])
        StockMovement.objects.create(
            product=self,
            quantity_change=delta,
            reason=reason,
            recorded_by=user,
            note=note,
        )


class StockMovement(models.Model):
    REASON_CHOICES = [
        ('SALE',        'Sale (consumption)'),
        ('RESTOCK',     'Restock / purchase'),
        ('ADJUSTMENT',  'Manual adjustment'),
        ('DAMAGE',      'Damaged / written off'),
    ]

    product         = models.ForeignKey(Product, related_name='stock_movements', on_delete=models.CASCADE)
    quantity_change = models.IntegerField(help_text="Positive = stock added, negative = stock removed.")
    reason          = models.CharField(max_length=20, choices=REASON_CHOICES, db_index=True)
    note            = models.CharField(max_length=255, blank=True)
    recorded_by     = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at      = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name}: {self.quantity_change:+d} ({self.reason})"
