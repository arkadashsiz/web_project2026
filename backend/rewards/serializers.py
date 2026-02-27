from rest_framework import serializers
from .models import Tip, RewardClaim


class TipSerializer(serializers.ModelSerializer):
    claim = serializers.SerializerMethodField(read_only=True)

    def get_claim(self, obj):
        claim = getattr(obj, 'claim', None)
        if not claim:
            return None
        request = self.context.get('request')
        if not request or request.user.id != obj.submitter_id:
            return None
        return {
            'unique_code': claim.unique_code,
            'amount': claim.amount,
            'is_paid': claim.is_paid,
        }

    def validate(self, attrs):
        case = attrs.get('case')
        suspect = attrs.get('suspect')
        if case and suspect and suspect.case_id != case.id:
            raise serializers.ValidationError('suspect must belong to selected case.')
        return attrs

    class Meta:
        model = Tip
        fields = '__all__'
        read_only_fields = ('submitter', 'assigned_detective')


class RewardClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardClaim
        fields = '__all__'
