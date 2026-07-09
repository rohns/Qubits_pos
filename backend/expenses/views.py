from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Expense
from .serializers import ExpenseSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.order_by('-date','-created_at')
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Same rule as sales: only staff can log an expense against a past date.
        Everyone else gets today's date regardless of what they submit, so a
        cashier can't quietly backdate an expense.
        """
        user = self.request.user
        if user.is_staff and serializer.validated_data.get('date'):
            serializer.save(recorded_by=user)
        else:
            serializer.save(recorded_by=user, date=timezone.localdate())

    def perform_update(self, serializer):
        """Non-staff can edit an expense's other fields, but not move its date."""
        user = self.request.user
        if user.is_staff:
            serializer.save()
        else:
            serializer.save(date=serializer.instance.date)
