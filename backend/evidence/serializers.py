from rest_framework import serializers
from .models import Evidence, Testimony, Biological, Vehicle, IDDocument

class BaseEvidenceSerializer(serializers.ModelSerializer):
    # These fields are set automatically by the server, users shouldn't send them
    collected_by = serializers.PrimaryKeyRelatedField(read_only=True)
    evidence_type = serializers.CharField(read_only=True)

    class Meta:
        model = Evidence
        fields = '__all__'

class TestimonySerializer(BaseEvidenceSerializer):
    class Meta(BaseEvidenceSerializer.Meta):
        model = Testimony

class BiologicalSerializer(BaseEvidenceSerializer):
    class Meta(BaseEvidenceSerializer.Meta):
        model = Biological

class VehicleSerializer(BaseEvidenceSerializer):
    class Meta(BaseEvidenceSerializer.Meta):
        model = Vehicle

    def validate(self, data):
        # Enforcing the document rule: Plate and Serial cannot exist simultaneously
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
