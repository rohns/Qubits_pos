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
