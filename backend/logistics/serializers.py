from rest_framework import serializers
from django.db.models import Max
from django.utils import timezone
from .models import CivilianTip, BailTransaction
from cases.models import Case, CaseSuspect
from users.models import User

class MostWantedSerializer(serializers.ModelSerializer):
    """
    Handles the display and calculation for Highly Wanted Suspects (Chapter 4.7).
    """
    max_crime_level_lj = serializers.SerializerMethodField()
    max_days_wanted_di = serializers.SerializerMethodField()
    ranking_score = serializers.SerializerMethodField()
    bounty_reward = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'max_crime_level_lj', 'max_days_wanted_di', 
            'ranking_score', 'bounty_reward'
        ]

    def get_max_crime_level_lj(self, obj):
        # Max crime level across ALL cases (Open or Closed) for this suspect
        # Case.crime_level is integer 1-4.
        max_level = obj.suspected_in_cases.aggregate(Max('crime_level'))['crime_level__max']
        return max_level if max_level else 0

    def get_max_days_wanted_di(self, obj):
        # Max days wanted for currently OPEN/WANTED cases
        # We look at CaseSuspect records where status implies 'wanted'
        active_records = CaseSuspect.objects.filter(
            suspect=obj,
            status__in=['WANTED', 'HIGHLY_WANTED']
        )
        if not active_records.exists():
            return 0
        
        # Calculate days for each and find max
        now = timezone.now()
        max_days = 0
        for record in active_records:
            delta = (now - record.date_marked_wanted).days
            if delta > max_days:
                max_days = delta
        return max_days

    def get_ranking_score(self, obj):
        # Formula: max(Lj) * max(Di)
        lj = self.get_max_crime_level_lj(obj)
        di = self.get_max_days_wanted_di(obj)
        return lj * di

    def get_bounty_reward(self, obj):
        # Formula: Ranking Score * 20,000,000 Rials
        score = self.get_ranking_score(obj)
        return score * 20_000_000

class CivilianTipSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CivilianTip
        fields = '__all__'
        read_only_fields = ['status', 'officer_reviewer', 'detective_reviewer', 'unique_token', 'reward_amount', 'user']

class RewardLookupSerializer(serializers.Serializer):
    national_id = serializers.CharField(max_length=20)
    unique_token = serializers.CharField(max_length=20)

class BailCreationSerializer(serializers.Serializer):
    case_suspect_id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1000)
