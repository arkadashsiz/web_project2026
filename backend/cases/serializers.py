from rest_framework import serializers
from .models import Case, Complaint, CrimeSceneReport, CaseSuspect

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'

class CaseSuspectSerializer(serializers.ModelSerializer):
    suspect_name = serializers.ReadOnlyField(source='suspect.username')
    
    class Meta:
        model = CaseSuspect
        fields = '__all__'

class CrimeSceneReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeSceneReport
        fields = '__all__'

class CaseSerializer(serializers.ModelSerializer):
    # Nested serializers allow us to see related data in one request
    suspects_list = CaseSuspectSerializer(source='casesuspect_set', many=True, read_only=True)
    
    class Meta:
        model = Case
        fields = '__all__'
