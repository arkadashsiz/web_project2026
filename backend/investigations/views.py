from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import EvidenceConnection, Trial
from .serializers import (
    EvidenceConnectionReadSerializer, EvidenceConnectionWriteSerializer, 
    TrialSerializer, MostWantedSerializer
)
from .permissions import IsDetective, IsSergeant, IsJudge, IsHighCommand

from cases.models import CaseSuspect, Case

class DetectiveBoardViewSet(viewsets.ModelViewSet):
    """
    Manages the 'Board'. Detectives link evidence to suspects here.
    """
    queryset = EvidenceConnection.objects.all()
    permission_classes = [IsDetective]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return EvidenceConnectionReadSerializer
        return EvidenceConnectionWriteSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class InvestigationOperationsViewSet(viewsets.GenericViewSet):
    """
    Handles Suspect Status Transitions and Interrogations.
    """
    queryset = CaseSuspect.objects.all()
    permission_classes = [IsDetective]

    @decorators.action(detail=True, methods=['post'], url_path='interrogate')
    def interrogate(self, request, pk=None):
        """
        Updates the detective score (Chapter 4.5).
        Input: {'score_delta': int}
        """
        suspect = self.get_object()
        score_delta = int(request.data.get('score_delta', 0))
        
        # Logic: Update detective_score
        current_score = suspect.detective_score or 0
        suspect.detective_score = current_score + score_delta
        suspect.save()
        
        return Response({
            "status": "Interrogation logged",
            "new_score": suspect.detective_score
        })

    @decorators.action(detail=True, methods=['post'], url_path='submit-review')
    def submit_to_sergeant(self, request, pk=None):
        """
        Moves suspect status from UNDER_INVESTIGATION to WAITING_REVIEW.
        Requires minimum evidence.
        """
        suspect = self.get_object()
        
        # Check if enough evidence is linked
        evidence_count = EvidenceConnection.objects.filter(suspect=suspect).count()
        if evidence_count < 1:
            return Response(
                {"error": "Cannot submit without linking at least one piece of evidence."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Updated field name: status
        suspect.status = 'WAITING_REVIEW' 
        suspect.save()
        return Response({"status": "Case file submitted to Sergeant."})

class SergeantReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Sergeant View: Lists suspects waiting for review.
    Allows Approve/Reject actions.
    """
    # Updated field name: status
    queryset = CaseSuspect.objects.filter(status='WAITING_REVIEW')
    serializer_class = MostWantedSerializer 
    permission_classes = [IsSergeant]

    @decorators.action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """ Moves to TRIAL_READY """
        suspect = self.get_object()
        # Updated field name: status
        suspect.status = 'TRIAL_READY'
        suspect.save()
        return Response({"status": "Approved for Trial"})

    @decorators.action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """ Returns to UNDER_INVESTIGATION """
        suspect = self.get_object()
        # Updated field name: status
        suspect.status = 'UNDER_INVESTIGATION'
        suspect.save()
        return Response({"status": "Rejected. Returned to Detective."})

class JudicialViewSet(viewsets.ModelViewSet):
    """
    Judicial View: Judges manage trials here.
    """
    queryset = Trial.objects.all()
    serializer_class = TrialSerializer
    permission_classes = [IsJudge]

    def perform_create(self, serializer):
        # Automatically set the judge to the current user
        serializer.save(judge=self.request.user, date_started=timezone.now().date())

    @decorators.action(detail=True, methods=['post'])
    def deliver_verdict(self, request, pk=None):
        """
        Finalizes the trial.
        Input: {'verdict': 'GUILTY', 'sentence_years': 5, 'notes': '...'}
        """
        trial = self.get_object()
        verdict = request.data.get('verdict')
        years = request.data.get('sentence_years', 0)
        
        trial.verdict = verdict
        trial.sentence_years = years
        trial.date_concluded = timezone.now().date()
        trial.court_transcripts = request.data.get('notes', '')
        trial.save()

        # Update the Suspect Status based on Verdict
        suspect = trial.case_suspect
        if verdict == 'GUILTY':
            suspect.status = 'CONVICTED' # Updated field name
            # Ideally, we might deactivate the user here if needed, but not required by strict prompt
        elif verdict == 'NOT_GUILTY':
            suspect.status = 'ACQUITTED' # Updated field name
        else:
            suspect.status = 'MISTRIAL' # Updated field name
            
        suspect.save()

        return Response({"status": f"Verdict delivered: {verdict}"})

class MostWantedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Chapter 4.7: Filters for Crime Level 4 (Severe) and applies threat formula.
    """
    serializer_class = MostWantedSerializer
    permission_classes = [IsHighCommand]

    def get_queryset(self):
        # Updated field name: status
        return CaseSuspect.objects.filter(
            case__crime_level=4
        ).exclude(
            status__in=['CONVICTED', 'ACQUITTED']
        )
