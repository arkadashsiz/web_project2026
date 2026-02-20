from rest_framework import serializers
from .models import Evidence, Testimony, Biological, Vehicle, IDDocument


class BaseEvidenceSerializer(serializers.ModelSerializer):
    collected_by = serializers.PrimaryKeyRelatedField(read_only=True)
    evidence_type = serializers.CharField(read_only=True)
    date_collected = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Evidence
        fields = '__all__'


class TestimonySerializer(BaseEvidenceSerializer):
    class Meta(BaseEvidenceSerializer.Meta):
        model = Testimony
        fields = '__all__'


class BiologicalSerializer(BaseEvidenceSerializer):
    class Meta(BaseEvidenceSerializer.Meta):
        model = Biological
        fields = '__all__'


class VehicleSerializer(BaseEvidenceSerializer):
    class Meta(BaseEvidenceSerializer.Meta):
        model = Vehicle
        fields = '__all__'

    def validate(self, data):
        plate = data.get('license_plate')
        serial = data.get('serial_number')

        if plate and serial:
            raise serializers.ValidationError(
                {"detail": "A vehicle cannot have both a license plate and a serial number simultaneously."}
            )
        if not plate and not serial:
            raise serializers.ValidationError(
                {"detail": "You must provide either a license plate or a serial number."}
            )

        return data


class IDDocumentSerializer(BaseEvidenceSerializer):
    class Meta(BaseEvidenceSerializer.Meta):
        model = IDDocument
        fields = '__all__'

from .models import WitnessStatement


class WitnessStatementSerializer(serializers.ModelSerializer):
    submitted_by = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)
    reviewed_by = serializers.PrimaryKeyRelatedField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = WitnessStatement
        fields = '__all__'
