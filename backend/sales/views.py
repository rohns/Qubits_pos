from collections import defaultdict

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Sale
from .serializers import SaleSerializer, CreateSaleSerializer

class SaleViewSet(viewsets.ModelViewSet):
    queryset           = Sale.objects.prefetch_related('items__product').order_by('-created_at')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return CreateSaleSerializer if self.action == 'create' else SaleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Allow staff to void/cancel a paid sale."""
        if not request.user.is_staff:
            return Response({'error': 'Only staff can cancel sales.'}, status=403)
        try:
            sale = Sale.objects.get(pk=pk)
        except Sale.DoesNotExist:
            return Response({'error': 'Sale not found.'}, status=404)
        if sale.status not in ('PAID', 'PENDING'):
            return Response({'error': f'Cannot cancel a sale with status {sale.status}.'}, status=400)
        sale.status = 'CANCELLED'
        sale.save()
        return Response({'message': f'Sale {sale.receipt_number} cancelled.', 'receipt_number': sale.receipt_number})

    @action(detail=False, methods=['get'])
    def credit(self, request):
        """
        The tab/credit ledger — every service given out but not yet paid for,
        with who owes, how much, and when it was offered. Settle one of these
        the normal way: call /api/payments/cash/ or /api/payments/mpesa-cash/
        with its sale_id once the customer pays.
        """
        qs = (
            Sale.objects.filter(payment_method='CREDIT', status='PENDING')
            .prefetch_related('items__product')
            .select_related('cashier')
        )
        name_filter = request.query_params.get('customer_name')
        if name_filter:
            qs = qs.filter(customer_name__icontains=name_filter)
        qs = qs.order_by('created_at')  # Oldest debt first

        results = []
        by_customer = defaultdict(lambda: {'total_owed': 0, 'count': 0})
        for sale in qs:
            amount = float(sale.total_amount)
            key = sale.customer_name or 'Unknown'
            by_customer[key]['total_owed'] += amount
            by_customer[key]['count'] += 1
            results.append({
                'sale_id': sale.id,
                'receipt_number': sale.receipt_number,
                'customer_name': sale.customer_name,
                'customer_phone': sale.customer_phone,
                'amount': round(amount, 2),
                'amount_display': f"KES {amount:,.2f}",
                'offered_at': sale.created_at,
                'cashier': sale.cashier.username if sale.cashier else None,
                'items': [
                    {'service': i.product.name, 'quantity': i.quantity}
                    for i in sale.items.all()
                ],
            })

        total_outstanding = sum(r['amount'] for r in results)

        return Response({
            'currency': 'KES',
            'total_outstanding': round(total_outstanding, 2),
            'total_outstanding_display': f"KES {total_outstanding:,.2f}",
            'count': len(results),
            'by_customer': [
                {
                    'customer_name': name,
                    'total_owed': round(v['total_owed'], 2),
                    'total_owed_display': f"KES {v['total_owed']:,.2f}",
                    'open_sales': v['count'],
                }
                for name, v in sorted(by_customer.items(), key=lambda kv: -kv[1]['total_owed'])
            ],
            'sales': results,
        })
