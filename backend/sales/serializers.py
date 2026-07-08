from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from products.models import Product
from .models import Sale, SaleItem


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
                  'status','payment_method','customer_phone','customer_name','created_at','sale_date','items']

    def get_cashier_name(self, obj):
        return obj.cashier.username if obj.cashier else None

class CreateSaleSerializer(serializers.Serializer):
    items          = serializers.ListField(child=serializers.DictField())
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    customer_name  = serializers.CharField(required=False, allow_blank=True)
    sale_date      = serializers.DateTimeField(required=False)  # Allow custom date (staff only)
    # The only payment_method a sale can be *created* with directly. Everything
    # else (CASH/MPESA) is set afterwards by the /payments/ endpoints once money
    # actually changes hands — this field exists purely to support "put it on
    # my tab" at the point of sale.
    payment_method = serializers.ChoiceField(choices=['CREDIT'], required=False)

    def validate(self, data):
        if data.get('payment_method') == 'CREDIT' and not data.get('customer_name', '').strip():
            raise serializers.ValidationError(
                "customer_name is required to record a sale on credit — you need a name to know who owes you."
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        items_data     = validated_data['items']
        customer_phone = validated_data.get('customer_phone', '')
        customer_name  = validated_data.get('customer_name', '').strip()
        sale_date      = validated_data.get('sale_date')  # Optional custom date
        is_credit      = validated_data.get('payment_method') == 'CREDIT'

        # Lock the products for this sale up front (ordered by id to avoid deadlocks
        # between concurrent sales that share products) so two cashiers can't both
        # oversell the last few units of a tracked-stock item.
        product_ids = [item['product_id'] for item in items_data]
        products_by_id = {
            p.id: p
            for p in Product.objects.select_for_update().filter(id__in=product_ids).order_by('id')
        }

        total = 0
        sale_items = []
        for item in items_data:
            product = products_by_id[item['product_id']]
            qty = int(item['quantity'])

            if product.track_stock and product.stock < qty:
                raise serializers.ValidationError(
                    f"Not enough stock for '{product.name}': {product.stock} left, {qty} requested."
                )

            line_total = product.price * qty
            total += line_total
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
            customer_name  = customer_name or None,
            payment_method = 'CREDIT' if is_credit else 'NONE',
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
            if product.track_stock:
                # Stock is still consumed immediately even on credit — the paper
                # or toner is used up whether or not the customer has paid yet.
                product.adjust_stock(
                    delta=-qty,
                    reason='SALE',
                    user=request.user,
                    note=f"Sale {sale.receipt_number or sale.id}",
                )
        return sale
