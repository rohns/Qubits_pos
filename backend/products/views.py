from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class   = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Product.objects.order_by('category','name')
        # Staff see all; cashiers only see active
        if not self.request.user.is_staff:
            qs = qs.filter(active=True)
        return qs
