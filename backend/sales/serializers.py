from rest_framework import serializers
from .models import Sale, SaleItem
from products.models import Product
from django.utils import timezone

class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model  = SaleItem
        fields = ['id','product','product_name','quantity','unit_price','line_total']

class SaleSerializer(serializers.ModelSerializer):
    items          = SaleItemSerializer(many=True, read_only=True)
    cashier_name   = serializers.SerializerMethodField()

    class Meta:
        model  = Sale
        fields = ['id','receipt_number','cashier','cashier_name','total_amount',
                  'status','payment_method','customer_phone','created_at','sale_date','items']

    def get_cashier_name(self, obj):
        return obj.cashier.username if obj.cashier else None

class CreateSaleSerializer(serializers.Serializer):
    items          = serializers.ListField(child=serializers.DictField())
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    sale_date      = serializers.DateTimeField(required=False)  # Allow custom date (staff only)

    def create(self, validated_data):
        request = self.context['request']
        items_data     = validated_data['items']
        customer_phone = validated_data.get('customer_phone', '')
        sale_date      = validated_data.get('sale_date')  # Optional custom date
        
        total = 0
        sale_items = []
        for item in items_data:
            product = Product.objects.get(id=item['product_id'])
            qty        = int(item['quantity'])
            line_total = product.price * qty
            total     += line_total
            sale_items.append((product, qty, product.price, line_total))

        # Use custom date if provided (staff only), otherwise current time
        if sale_date and request.user.is_staff:
            created_at = sale_date
        else:
            created_at = timezone.now()

        sale = Sale.objects.create(
            cashier        = request.user,
            total_amount   = total,
            customer_phone = customer_phone or None,
            created_at     = created_at,
        )
        
        for product, qty, unit_price, line_total in sale_items:
            SaleItem.objects.create(
                sale       = sale,
                product    = product,
                quantity   = qty,
                unit_price = unit_price,
                line_total = line_total,
            )
        return sale
