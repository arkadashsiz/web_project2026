# investigation/serializers.py
from rest_framework import serializers
from django.utils import timezone

from .models import DetectiveBoard, BoardItem, BoardConnection, Interrogation, Trial
from cases.models import CaseSuspect


class BoardItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardItem
        fields = '__all__'


class BoardConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardConnection
        fields = '__all__'


class DetectiveBoardSerializer(serializers.ModelSerializer):
    items = BoardItemSerializer(many=True, read_only=True)
    connections = BoardConnectionSerializer(many=True, read_only=True)

    class Meta:
        model = DetectiveBoard
        fields = '__all__'


class InterrogationSerializer(serializers.ModelSerializer):
    detective_name = serializers.ReadOnlyField(source='detective.get_full_name')
    sergeant_name = serializers.ReadOnlyField(source='sergeant.get_full_name')

    class Meta:
        model = Interrogation
        fields = '__all__'
        read_only_fields = ['case_suspect', 'detective', 'sergeant', 'captain_approved_by', 'chief_approved_by']


class TrialSerializer(serializers.ModelSerializer):
    judge_name = serializers.ReadOnlyField(source='judge.get_full_name')

    class Meta:
        model = Trial
        fields = '__all__'
        read_only_fields = ['judge']


class MostWantedSerializer(serializers.ModelSerializer):
    suspect_name = serializers.CharField(source='suspect.get_full_name', read_only=True)
    crime_level = serializers.IntegerField(source='case.crime_level', read_only=True)
    detective_guilt_score = serializers.SerializerMethodField()
    days_wanted = serializers.SerializerMethodField()
    rank_score = serializers.SerializerMethodField()
    reward_rials = serializers.SerializerMethodField()

    class Meta:
        model = CaseSuspect
        fields = [
            'id', 'suspect_name', 'case', 'crime_level',
            'wanted_since', 'days_wanted', 'detective_guilt_score',
            'rank_score', 'reward_rials'
        ]

    def get_detective_guilt_score(self, obj):
        try:
            if obj.interrogation and obj.interrogation.detective_score:
                return obj.interrogation.detective_score
        except Exception:
            pass
        return 0

    def get_days_wanted(self, obj):
        wanted_since = getattr(obj, 'wanted_since', None)
        if not wanted_since:
            return 0
        delta = timezone.now() - wanted_since
        return max(delta.days, 0)

    def get_rank_score(self, obj):
        # Formula: L_j * D_i  (with mapping: 3->1, 2->2, 1->3, 0->4; default 1)
        level_map = {3: 1, 2: 2, 1: 3, 0: 4}  # 0 is Critical Level
        lj = level_map.get(getattr(obj.case, 'crime_level', 3), 1)
        di = self.get_days_wanted(obj)
        return lj * di

    def get_reward_rials(self, obj):
        # Formula: Rank * 20,000,000
        return self.get_rank_score(obj) * 20000000
