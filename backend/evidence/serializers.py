from rest_framework import serializers
from .models import WitnessEvidence, BiologicalEvidence, VehicleEvidence, IdentificationEvidence, OtherEvidence


class EvidenceBaseValidationMixin:
    def validate(self, attrs):
        title = (attrs.get('title') or '').strip()
        description = (attrs.get('description') or '').strip()
        if not title:
            raise serializers.ValidationError({'title': 'Title is required.'})
        if not description:
            raise serializers.ValidationError({'description': 'Description is required.'})
        return attrs


class WitnessEvidenceSerializer(EvidenceBaseValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = WitnessEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        transcript = (attrs.get('transcript') or '').strip()
        media_items = attrs.get('media_items', [])
        media_url = (attrs.get('media_url') or '').strip()

        if not transcript and not media_items and not media_url:
            raise serializers.ValidationError('Witness evidence should include transcript and/or local media (image/video/audio).')

        if media_items and not isinstance(media_items, list):
            raise serializers.ValidationError({'media_items': 'media_items must be a list.'})
        for item in media_items or []:
            if not isinstance(item, dict):
                raise serializers.ValidationError({'media_items': 'Each media item must be an object.'})
            media_type = item.get('type')
            if media_type not in ['image', 'video', 'audio']:
                raise serializers.ValidationError({'media_items': 'type must be one of image/video/audio.'})
            if not item.get('url'):
                raise serializers.ValidationError({'media_items': 'Each media item must have a url.'})
        return attrs


class BiologicalEvidenceSerializer(EvidenceBaseValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = BiologicalEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        image_urls = attrs.get('image_urls', [])
        if not isinstance(image_urls, list) or len(image_urls) == 0:
            raise serializers.ValidationError({'image_urls': 'At least one image is required for biological evidence.'})

        allow_results_update = self.context.get('allow_results_update', False)
        has_forensic = 'forensic_result' in attrs and (attrs.get('forensic_result') or '').strip() != ''
        has_identity = 'identity_db_result' in attrs and (attrs.get('identity_db_result') or '').strip() != ''

        if self.instance is None and (has_forensic or has_identity):
            raise serializers.ValidationError('forensic_result and identity_db_result must be empty when biological evidence is created.')

        if self.instance is not None and not allow_results_update and (has_forensic or has_identity):
            raise serializers.ValidationError('Biological results can only be updated by forensic endpoint.')
        return attrs


class VehicleEvidenceSerializer(EvidenceBaseValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = VehicleEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        plate_number = (attrs.get('plate_number') or '').strip()
        serial_number = (attrs.get('serial_number') or '').strip()
        if bool(plate_number) == bool(serial_number):
            raise serializers.ValidationError('Exactly one of plate_number or serial_number must be set.')
        return attrs


class IdentificationEvidenceSerializer(EvidenceBaseValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = IdentificationEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        metadata = attrs.get('metadata', {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise serializers.ValidationError({'metadata': 'metadata must be a key-value object.'})
        return attrs


class OtherEvidenceSerializer(EvidenceBaseValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = OtherEvidence
        fields = '__all__'
        read_only_fields = ('recorded_by', 'recorded_at')
