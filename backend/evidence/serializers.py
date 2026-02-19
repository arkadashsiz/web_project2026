from rest_framework import serializers
from .models import Evidence, Testimony, Biological, Vehicle, IDDocument

class EvidenceSerializer(serializers.ModelSerializer):
    # Base serializer
    class Meta:
        model = Evidence
        fields = '__all__'

class TestimonySerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimony
        fields = '__all__'

class BiologicalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Biological
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class IDDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDDocument
        fields = '__all__'
