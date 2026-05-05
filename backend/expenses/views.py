from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Expense
from .serializers import ExpenseSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.order_by('-date','-created_at')
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
