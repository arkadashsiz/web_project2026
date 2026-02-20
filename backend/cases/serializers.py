from rest_framework import serializers
from .models import Case, Complaint, CrimeSceneReport, CaseSuspect


class ComplaintSerializer(serializers.ModelSerializer):
    complainant_username = serializers.ReadOnlyField(source='complainant.username')

    class Meta:
        model = Complaint
        fields = [
            'id', 'complainant', 'complainant_username', 'details',
            'status', 'cadet_message', 'rejection_count',
            'target_case', 'created_at'
        ]
        read_only_fields = [
            'complainant',
            'status',
            'cadet_message',
            'rejection_count',
            'target_case',
            'created_at'
        ]


class ComplaintReviewSerializer(serializers.Serializer):
    ACTION_CHOICES = (
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    error_message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data.get('action') == 'reject' and not data.get('error_message'):
            raise serializers.ValidationError({
                "error_message": "An error message is required when rejecting a complaint."
            })
        return data


class CrimeSceneReportSerializer(serializers.ModelSerializer):
    reporting_officer_username = serializers.ReadOnlyField(source='reporting_officer.username')

    class Meta:
        model = CrimeSceneReport
        fields = [
            'id', 'reporting_officer', 'reporting_officer_username',
            'scene_datetime', 'location_details', 'report_details',
            'status', 'case', 'created_at'
        ]
        read_only_fields = [
            'reporting_officer',
            'status',
            'case',
            'created_at'
        ]


class CrimeSceneReviewSerializer(serializers.Serializer):
    ACTION_CHOICES = (
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)


class CaseSuspectSerializer(serializers.ModelSerializer):
    suspect_username = serializers.ReadOnlyField(source='suspect.username')

    class Meta:
        model = CaseSuspect
        fields = [
            'id', 'case', 'suspect', 'suspect_username',
            'status', 'date_marked_wanted'
        ]
        read_only_fields = ['date_marked_wanted']


class CaseSerializer(serializers.ModelSerializer):
    suspects_list = CaseSuspectSerializer(source='casesuspect_set', many=True, read_only=True)
    lead_detective_username = serializers.ReadOnlyField(source='lead_detective.username')

    class Meta:
        model = Case
        fields = [
            'id', 'title', 'description', 'crime_level', 'status',
            'lead_detective', 'lead_detective_username', 'assigned_personnel',
            'complainants', 'suspects_list', 'creation_date', 'last_updated'
        ]
        read_only_fields = ['status', 'creation_date', 'last_updated']
