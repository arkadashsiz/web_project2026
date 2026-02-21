from rest_framework import serializers
from .models import DetectiveBoard, BoardNode, BoardEdge, Suspect, Interrogation, Notification


class BoardNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardNode
        fields = '__all__'


class BoardEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardEdge
        fields = '__all__'


class DetectiveBoardSerializer(serializers.ModelSerializer):
    nodes = BoardNodeSerializer(many=True, read_only=True)
    edges = BoardEdgeSerializer(many=True, read_only=True)

    class Meta:
        model = DetectiveBoard
        fields = ('id', 'case', 'detective', 'exported_image_url', 'updated_at', 'nodes', 'edges')


class SuspectSerializer(serializers.ModelSerializer):
    days_wanted = serializers.SerializerMethodField()

    def get_days_wanted(self, obj):
        return obj.days_wanted()

    class Meta:
        model = Suspect
        fields = '__all__'


class InterrogationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interrogation
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
