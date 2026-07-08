from rest_framework import serializers
from .models import Product, StockMovement

class ProductSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'price', 'category', 'active', 'is_service', 'created_at',
            'stock', 'track_stock', 'reorder_level', 'is_low_stock',
        ]


class StockAdjustmentSerializer(serializers.Serializer):
    """Used by the restock/adjust-stock endpoint."""
    quantity_change = serializers.IntegerField(help_text="Positive to add stock, negative to remove.")
    reason = serializers.ChoiceField(choices=StockMovement.REASON_CHOICES, default='RESTOCK')
    note = serializers.CharField(required=False, allow_blank=True, default="")


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    recorded_by_username = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = ['id', 'product', 'product_name', 'quantity_change', 'reason', 'note',
                  'recorded_by_username', 'created_at']

    def get_recorded_by_username(self, obj):
        return obj.recorded_by.username if obj.recorded_by else None
