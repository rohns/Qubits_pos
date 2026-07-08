from django.db import models as django_models
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Product, StockMovement
from .serializers import ProductSerializer, StockAdjustmentSerializer, StockMovementSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class   = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Product.objects.order_by('category', 'name')
        # Staff see all; cashiers only see active
        if not self.request.user.is_staff:
            qs = qs.filter(active=True)
        return qs

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Products where track_stock is on and stock has fallen to/below reorder_level."""
        qs = (
            Product.objects.filter(track_stock=True)
            .filter(stock__lte=django_models.F('reorder_level'))
            .order_by('stock')
        )
        return Response(ProductSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='adjust-stock')
    def adjust_stock(self, request, pk=None):
        """Restock, write off, or manually correct a product's stock, with an audit trail."""
        product = self.get_object()
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product.adjust_stock(
            delta=serializer.validated_data['quantity_change'],
            reason=serializer.validated_data['reason'],
            user=request.user,
            note=serializer.validated_data.get('note', ''),
        )
        return Response(ProductSerializer(product).data)

    @action(detail=True, methods=['get'], url_path='stock-movements')
    def stock_movements(self, request, pk=None):
        product = self.get_object()
        movements = product.stock_movements.all()[:100]
        return Response(StockMovementSerializer(movements, many=True).data)


class StockMovementListView(generics.ListAPIView):
    """All stock movements across all products, most recent first."""
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    queryset = StockMovement.objects.select_related('product', 'recorded_by').all()[:200]
