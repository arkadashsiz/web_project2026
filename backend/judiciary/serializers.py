from rest_framework import serializers
from .models import CourtSession


class CourtSessionSerializer(serializers.ModelSerializer):
    convicted_suspect_name = serializers.SerializerMethodField(read_only=True)

    def get_convicted_suspect_name(self, obj):
        return obj.convicted_suspect.full_name if obj.convicted_suspect else None

    def validate(self, attrs):
        case = attrs.get('case') or getattr(self.instance, 'case', None)
        verdict = attrs.get('verdict') or getattr(self.instance, 'verdict', None)
        convicted_suspect = attrs.get('convicted_suspect')

        if not convicted_suspect:
            raise serializers.ValidationError({'convicted_suspect': 'Select suspect for this verdict.'})
        if convicted_suspect and case and convicted_suspect.case_id != case.id:
            raise serializers.ValidationError({'convicted_suspect': 'Selected suspect does not belong to this case.'})
        if case and convicted_suspect:
            qs = CourtSession.objects.filter(case=case, convicted_suspect=convicted_suspect)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError({'convicted_suspect': 'This suspect already has a final court verdict.'})
        return attrs

    class Meta:
        model = CourtSession
        fields = '__all__'
        read_only_fields = ('judge',)
