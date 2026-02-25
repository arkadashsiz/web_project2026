from rest_framework import serializers
from .models import BailPayment


class BailPaymentSerializer(serializers.ModelSerializer):
    def validate_amount(self, value):
        if value is None:
            raise serializers.ValidationError('Amount is required.')
        if int(value) < 1000:
            raise serializers.ValidationError('Amount must be at least 1000.')
        return value

    class Meta:
        model = BailPayment
        fields = '__all__'
        read_only_fields = ('created_by', 'authority', 'gateway_status', 'payment_ref', 'status', 'created_at')
