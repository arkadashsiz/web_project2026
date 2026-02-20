from rest_framework import serializers
from django.db import transaction
from .models import EvidenceConnection, Trial
from evidence.models import Evidence, Testimony, Biological, Vehicle, IDDocument
from evidence.serializers import (
    BaseEvidenceSerializer, TestimonySerializer, BiologicalSerializer, 
    VehicleSerializer, IDDocumentSerializer
)

class EvidenceConnectionReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading the Detective Board.
    It dynamically selects the correct serializer based on Evidence Type.
    """
    evidence_details = serializers.SerializerMethodField()

    class Meta:
        model = EvidenceConnection
        fields = ['id', 'case', 'suspect', 'evidence', 'evidence_details', 'strength', 'notes', 'created_at']

    def get_evidence_details(self, obj):
        evidence_instance = obj.evidence
        if hasattr(evidence_instance, 'testimony'):
            return TestimonySerializer(evidence_instance.testimony).data
        elif hasattr(evidence_instance, 'biological'):
            return BiologicalSerializer(evidence_instance.biological).data
        elif hasattr(evidence_instance, 'vehicle'):
            return VehicleSerializer(evidence_instance.vehicle).data
        elif hasattr(evidence_instance, 'iddocument'):
            return IDDocumentSerializer(evidence_instance.iddocument).data
        else:
            return BaseEvidenceSerializer(evidence_instance).data

class EvidenceConnectionWriteSerializer(serializers.ModelSerializer):
    """ Serializer for creating links on the board. """
    class Meta:
        model = EvidenceConnection
        fields = ['case', 'suspect', 'evidence', 'strength', 'notes']

    def validate(self, data):
        if data['evidence'].case != data['case']:
            raise serializers.ValidationError("The evidence does not belong to the selected case.")
        return data

class TrialSerializer(serializers.ModelSerializer):
    judge_name = serializers.CharField(source='judge.get_full_name', read_only=True)

    class Meta:
        model = Trial
        fields = '__all__'
        read_only_fields = ['judge'] 

class MostWantedSerializer(serializers.Serializer):
    """
    Read-only serializer for the Most Wanted list (Crime Level 4).
    Calculates a threat score based on Interrogation (detective_score) and Evidence.
    """
    suspect_name = serializers.CharField(source='suspect.get_full_name') 
    case_title = serializers.CharField(source='case.title')
    # Mapped 'detective_score' from your model to 'interrogation_score' for the API
    interrogation_score = serializers.IntegerField(source='detective_score')
    evidence_count = serializers.IntegerField(source='evidence_links.count')
    threat_score = serializers.SerializerMethodField()

    def get_threat_score(self, obj):
        # Formula: (Detective Score * 1.5) + (Linked Evidence * 10)
        i_score = obj.detective_score or 0
        e_count = obj.evidence_links.count()
        return round((i_score * 1.5) + (e_count * 10))
