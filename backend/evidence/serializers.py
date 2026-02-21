from rest_framework import serializers
from .models import WitnessEvidence, BiologicalEvidence, VehicleEvidence, IdentificationEvidence, OtherEvidence


class WitnessEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WitnessEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')


class BiologicalEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiologicalEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')


class VehicleEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')


class IdentificationEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentificationEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')


class OtherEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')
