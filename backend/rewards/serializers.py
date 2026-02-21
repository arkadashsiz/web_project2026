from rest_framework import serializers
from .models import Tip, RewardClaim


class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = '__all__'
        read_only_fields = ('submitter',)


class RewardClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardClaim
        fields = '__all__'
