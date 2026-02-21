from rest_framework import serializers
from .models import Case, ComplaintSubmission, CaseComplainant, CaseWitness, CaseLog


class CaseComplainantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseComplainant
        fields = ('id', 'user', 'status', 'review_note')


class CaseWitnessSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseWitness
        fields = ('id', 'full_name', 'national_id', 'phone', 'statement')


class ComplaintSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintSubmission
        fields = ('id', 'case', 'complainant', 'attempt_count', 'stage', 'intern_note', 'officer_note', 'last_error_message')
        read_only_fields = ('attempt_count',)


class CaseSerializer(serializers.ModelSerializer):
    complainants = CaseComplainantSerializer(many=True, read_only=True)
    witnesses = CaseWitnessSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = (
            'id', 'title', 'description', 'source', 'status', 'severity',
            'created_by', 'assigned_detective', 'created_at', 'updated_at',
            'complainants', 'witnesses'
        )
        read_only_fields = ('created_by',)


class CaseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseLog
        fields = ('id', 'actor', 'action', 'details', 'created_at')
