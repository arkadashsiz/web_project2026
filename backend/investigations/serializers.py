from rest_framework import serializers
from .models import DetectiveBoard, Interrogation, Trial

class DetectiveBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectiveBoard
        fields = '__all__'

class InterrogationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interrogation
        fields = '__all__'

class TrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trial
        fields = '__all__'
