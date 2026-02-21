from rest_framework import serializers
from .models import CourtSession


class CourtSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtSession
        fields = '__all__'
        read_only_fields = ('judge',)
