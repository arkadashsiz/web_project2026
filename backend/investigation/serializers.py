from rest_framework import serializers
from .models import DetectiveBoard, BoardNode, BoardEdge, Suspect, Interrogation, Notification, SuspectSubmission


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
    def validate(self, attrs):
        for field in ['detective_score', 'sergeant_score', 'captain_score']:
            if field in attrs and attrs[field] is not None:
                val = int(attrs[field])
                if val < 1 or val > 10:
                    raise serializers.ValidationError({field: 'Score must be between 1 and 10.'})
        return attrs

    class Meta:
        model = Interrogation
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class SuspectSubmissionSerializer(serializers.ModelSerializer):
    suspect_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    suspect_brief = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SuspectSubmission
        fields = (
            'id', 'case', 'detective', 'suspects', 'suspect_ids',
            'suspect_brief', 'detective_reason', 'status',
            'sergeant', 'sergeant_message', 'created_at', 'reviewed_at',
        )
        read_only_fields = ('detective', 'suspects', 'status', 'sergeant', 'created_at', 'reviewed_at')

    def get_suspect_brief(self, obj):
        return [{'id': s.id, 'full_name': s.full_name, 'status': s.status} for s in obj.suspects.all()]
