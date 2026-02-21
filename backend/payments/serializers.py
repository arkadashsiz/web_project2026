from rest_framework import serializers
from .models import BailPayment


class BailPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BailPayment
        fields = '__all__'
        read_only_fields = ('created_by',)
