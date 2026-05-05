from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    # FIX: expose the username so frontend can display "Logged by"
    recorded_by_username = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['recorded_by', 'created_at', 'recorded_by_username']

    def get_recorded_by_username(self, obj):
        return obj.recorded_by.username if obj.recorded_by else None
