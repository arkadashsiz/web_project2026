from django.utils import timezone
from rest_framework import viewsets, decorators, status, mixins
from rest_framework.response import Response

from cases.models import CaseSuspect
from cases.serializers import CaseSuspectSerializer

from .models import DetectiveBoard, Interrogation, Trial
from .serializers import (
    DetectiveBoardSerializer,
    InterrogationSerializer,
    TrialSerializer,
    MostWantedSerializer,
)
from .permissions import IsDetective, IsSergeant, IsCaptain, IsChief, IsJudge


def get_cs_status(name: str) -> str:
    """
    Helper to safely reference CaseSuspect.Status enum if present.
    Falls back to raw string if enum or attribute isn't available.
    """
    Status = getattr(CaseSuspect, 'Status', None)
    if Status is not None and hasattr(Status, name):
        return getattr(Status, name)
    return name


class DetectiveBoardViewSet(viewsets.ModelViewSet):
    queryset = DetectiveBoard.objects.all()
    serializer_class = DetectiveBoardSerializer
    permission_classes = [IsDetective]

    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.request.query_params.get('case')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs


class InvestigationWorkflowViewSet(mixins.ListModelMixin,
                                   mixins.RetrieveModelMixin,
                                   viewsets.GenericViewSet):
    """
    Handles the Arrest Request, Interrogation, and Approval workflows.
    Operates on the CaseSuspect model to change statuses and generate Interrogations.
    Provides GET list/retrieve for role-based queues.
    """
    queryset = CaseSuspect.objects.select_related('case').all()
    serializer_class = CaseSuspectSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        case_id = self.request.query_params.get('case')
        if status_param:
            qs = qs.filter(status=status_param)
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsDetective])
    def request_arrest_warrant(self, request, pk=None):
        suspect = self.get_object()
        # Only allowed from UNDER_INVESTIGATION
        allowed_from = [get_cs_status('UNDER_INVESTIGATION')]
        if suspect.status not in allowed_from:
            return Response({"error": "Invalid status for arrest warrant request."}, status=status.HTTP_400_BAD_REQUEST)

        suspect.status = get_cs_status('WAITING_SERGEANT')
        # Set wanted_since if not set
        if not getattr(suspect, 'wanted_since', None):
            setattr(suspect, 'wanted_since', timezone.now())
        suspect.save()
        return Response({"message": "Sent to Sergeant for arrest warrant approval."})

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsSergeant])
    def sergeant_approve_arrest(self, request, pk=None):
        suspect = self.get_object()
        if suspect.status != get_cs_status('WAITING_SERGEANT'):
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        # Align with agreed flow: move to SERGEANT_APPROVED, create interrogation file
        suspect.status = get_cs_status('SERGEANT_APPROVED')
        suspect.save()

        Interrogation.objects.get_or_create(case_suspect=suspect)
        return Response({"message": "Sergeant Approved. Interrogation file created."})

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsDetective])
    def detective_update_interrogation(self, request, pk=None):
        """
        Optional convenience action: detective sets score/notes.
        """
        return self._update_interrogation(request, pk, role='detective')

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsSergeant])
    def sergeant_update_interrogation(self, request, pk=None):
        """
        Optional convenience action: sergeant sets score/notes.
        """
        return self._update_interrogation(request, pk, role='sergeant')

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsDetective | IsSergeant])
    def submit_interrogation(self, request, pk=None):
        """
        Unified action: either Detective or Sergeant can post a score and notes.
        When both scores are present, move to WAITING_CAPTAIN.
        """
        # Keep your original endpoint name but fix logic
        return self._update_interrogation(request, pk, role='auto')

    def _update_interrogation(self, request, pk, role: str):
        suspect = self.get_object()

        if suspect.status not in [get_cs_status('SERGEANT_APPROVED'), get_cs_status('WAITING_CAPTAIN')]:
            return Response({"error": "Interrogation allowed only after Sergeant approval."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interrogation = suspect.interrogation
        except Interrogation.DoesNotExist:
            return Response({"error": "Interrogation file not found. Ask Sergeant to approve arrest first."}, status=status.HTTP_400_BAD_REQUEST)

        # Parse inputs
        score = request.data.get('score')
        notes = request.data.get('notes', '')
        try:
            score = int(score)
        except (TypeError, ValueError):
            return Response({"error": "Valid score (1-10) is required."}, status=status.HTTP_400_BAD_REQUEST)

        if score < 1 or score > 10:
            return Response({"error": "Valid score (1-10) is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Determine which role is updating
        access_level = getattr(request.user, 'access_level', 0)
        performer = None
        if role == 'detective' or (role == 'auto' and access_level >= 40 and access_level < 60):
            interrogation.detective_score = score
            interrogation.detective_notes = notes
            interrogation.detective = request.user
            performer = 'Detective'
        elif role == 'sergeant' or (role == 'auto' and access_level >= 60 and access_level < 70):
            interrogation.sergeant_score = score
            interrogation.sergeant_notes = notes
            interrogation.sergeant = request.user
            performer = 'Sergeant'
        else:
            return Response({"error": "Unauthorized role for this action."}, status=status.HTTP_403_FORBIDDEN)

        interrogation.save()

        if interrogation.is_fully_evaluated():
            # Move to WAITING_CAPTAIN (minimal change consistent with your original logic)
            suspect.status = get_cs_status('WAITING_CAPTAIN')
            suspect.save()
            return Response({"message": f"{performer} evaluation saved. Both evaluations done. Sent to Captain."})

        return Response({"message": f"{performer} evaluation saved. Waiting for counterpart."})

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsCaptain])
    def captain_review(self, request, pk=None):
        suspect = self.get_object()
        if suspect.status != get_cs_status('WAITING_CAPTAIN'):
            return Response({"error": "Not waiting for Captain."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interrogation = suspect.interrogation
        except Interrogation.DoesNotExist:
            return Response({"error": "Interrogation file missing."}, status=status.HTTP_400_BAD_REQUEST)

        interrogation.captain_approved_by = request.user
        interrogation.save()

        # For simplicity and to avoid new statuses, proceed to TRIAL_READY.
        # If you still require Chief endorsement for critical cases, you can call chief_review optionally.
        suspect.status = get_cs_status('TRIAL_READY')
        suspect.save()

        msg = "Approved by Captain. Ready for Trial."
        if getattr(suspect.case, 'crime_level', None) == 0:
            msg += " (Critical case: Chief endorsement recommended.)"
        return Response({"message": msg})

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsChief])
    def chief_review(self, request, pk=None):
        suspect = self.get_object()
        # Allow Chief endorsement when TRIAL_READY (to avoid introducing a new WAITING_CHIEF status)
        if suspect.status != get_cs_status('TRIAL_READY'):
            return Response({"error": "Chief can endorse only when case is Trial Ready."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interrogation = suspect.interrogation
        except Interrogation.DoesNotExist:
            return Response({"error": "Interrogation file missing."}, status=status.HTTP_400_BAD_REQUEST)

        interrogation.chief_approved_by = request.user
        interrogation.save()

        return Response({"message": "Chief endorsement recorded."})


class TrialViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    """
    Chapter 4.6: Judiciary Workflow
    We operate on CaseSuspect in TRIAL_READY state and upsert a Trial record.
    Provides GET list/retrieve for judges.
    """
    queryset = CaseSuspect.objects.all()
    permission_classes = [IsJudge]

    def get_queryset(self):
        qs = super().get_queryset()
        # Only suspects that are Trial Ready should appear to judges
        return qs.filter(status=get_cs_status('TRIAL_READY'))

    def get_serializer_class(self):
        # For list/retrieve, show suspect data; for submit_verdict, return trial info
        if self.action in ['list', 'retrieve']:
            return CaseSuspectSerializer
        return TrialSerializer

    def _validate_and_apply_verdict(self, suspect, verdict, sentence_years, notes, judge):
        # Upsert Trial
        trial, created = Trial.objects.get_or_create(case_suspect=suspect, defaults={
            'judge': judge,
            'verdict': verdict,
            'sentence_years': sentence_years,
            'judge_notes': notes,
        })
        if not created:
            trial.judge = judge
            trial.verdict = verdict
            trial.sentence_years = sentence_years
            trial.judge_notes = notes
            trial.save()

        # Update CaseSuspect status mapping
        if verdict == 'GUILTY':
            suspect.status = get_cs_status('CONVICTED')
        elif verdict == 'NOT_GUILTY':
            suspect.status = get_cs_status('ACQUITTED')
        else:
            suspect.status = get_cs_status('MISTRIAL')
        suspect.save()
        return trial

    @decorators.action(detail=True, methods=['post'])
    def submit_verdict(self, request, pk=None):
        suspect = self.get_object()

        # Optionally ensure it's Trial Ready
        if suspect.status != get_cs_status('TRIAL_READY'):
            return Response({"error": "Suspect is not Trial Ready."}, status=status.HTTP_400_BAD_REQUEST)

        verdict = request.data.get('verdict')
        notes = request.data.get('notes', '')
        sentence = request.data.get('sentence_years', 0)

        if verdict not in ['GUILTY', 'NOT_GUILTY', 'MISTRIAL']:
            return Response({"error": "Verdict must be GUILTY, NOT_GUILTY or MISTRIAL."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            sentence = int(sentence)
        except (TypeError, ValueError):
            return Response({"error": "sentence_years must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        if verdict == 'NOT_GUILTY' and sentence != 0:
            return Response({"error": "Sentence must be 0 if NOT_GUILTY."}, status=status.HTTP_400_BAD_REQUEST)
        if verdict == 'GUILTY' and sentence < 0:
            return Response({"error": "Sentence must be >= 0."}, status=status.HTTP_400_BAD_REQUEST)

        trial = self._validate_and_apply_verdict(
            suspect=suspect,
            verdict=verdict,
            sentence_years=sentence,
            notes=notes,
            judge=request.user
        )
        data = TrialSerializer(trial, context={'request': request}).data
        return Response({"message": f"Trial concluded. Verdict: {verdict}", "trial": data}, status=status.HTTP_200_OK)


class MostWantedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Chapter 4.7: Most Wanted List
    Minimal-change: keep original idea but return a QuerySet (not a Python list).
    """
    serializer_class = MostWantedSerializer
    permission_classes = [IsCaptain]  # High Command 80+

    def get_queryset(self):
        # Suspects who are in waiting-for-sergeant stage and have a wanted_since date
        qs = CaseSuspect.objects.all()
        status_waiting_sergeant = get_cs_status('WAITING_SERGEANT')
        qs = qs.filter(status=status_waiting_sergeant).exclude(wanted_since__isnull=True)

        # Optional: if your Case has crime_level and you want to focus on higher levels, filter here
        # qs = qs.filter(case__crime_level__in=[0, 1, 2, 3, 4])

        # Keep it DB-level sortable; serializer will compute rank
        return qs.order_by('-wanted_since')
