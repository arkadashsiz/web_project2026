from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from drf_spectacular.utils import extend_schema

from .models import Complaint, Case, CrimeSceneReport
from .serializers import (
    ComplaintSerializer, ComplaintReviewSerializer,
    CrimeSceneReportSerializer, CrimeSceneReviewSerializer,
    CaseSerializer
)

class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Complaint.objects.none()

        user = self.request.user
        
        if user.access_level == 0:  # Civilian
            return Complaint.objects.filter(complainant=user)
        elif user.access_level == 10:  # Cadet
            return Complaint.objects.filter(
                status__in=[Complaint.Status.PENDING_CADET, Complaint.Status.RETURNED_TO_CADET]
            )
        elif user.access_level >= 20:  # Officer and above
            return Complaint.objects.filter(
                status__in=[Complaint.Status.PENDING_OFFICER, Complaint.Status.APPROVED, Complaint.Status.ARCHIVED]
            )
            
        return Complaint.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        
        archived_count = Complaint.objects.filter(
            complainant=user, 
            status=Complaint.Status.ARCHIVED
        ).count()
        
        if archived_count >= 3:
            raise PermissionDenied("You have reached the maximum number of archived complaints and are blocked from submitting new ones.")

        serializer.save(complainant=user, status=Complaint.Status.PENDING_CADET)

    @extend_schema(request=ComplaintReviewSerializer, responses={200: ComplaintSerializer})
    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """Hierarchical workflow for reviewing complaints (Cadets & Officers)."""
        complaint = self.get_object()
        user = request.user
        
        serializer = ComplaintReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        error_message = serializer.validated_data.get('error_message', '')

        # ---- CADET REVIEW LOGIC (Level 10) ----
        if user.access_level == 10:
            if complaint.status not in [Complaint.Status.PENDING_CADET, Complaint.Status.RETURNED_TO_CADET]:
                return Response({"detail": "Cadets can only review pending cadet complaints."}, status=status.HTTP_400_BAD_REQUEST)
            
            if action_type == 'reject':
                complaint.cadet_message = error_message
                complaint.rejection_count += 1
                if complaint.rejection_count >= 3:
                    complaint.status = Complaint.Status.ARCHIVED
                else:
                    complaint.status = Complaint.Status.RETURNED_TO_COMPLAINANT
            elif action_type == 'approve':
                complaint.cadet_message = ''
                complaint.status = Complaint.Status.PENDING_OFFICER

        # ---- OFFICER REVIEW LOGIC (Level 20+) ----
        elif user.access_level >= 20:
            if complaint.status != Complaint.Status.PENDING_OFFICER:
                return Response({"detail": "Officers can only review pending officer complaints."}, status=status.HTTP_400_BAD_REQUEST)
            
            if action_type == 'reject':
                complaint.status = Complaint.Status.RETURNED_TO_CADET
                complaint.cadet_message = error_message
            elif action_type == 'approve':
                with transaction.atomic():
                    complaint.status = Complaint.Status.APPROVED
                    
                    new_case = Case.objects.create(
                        title=f"Case for Complaint #{complaint.id}",
                        description=complaint.details,
                        investigating_officer=user
                    )
                    new_case.complainants.add(complaint.complainant)
                    
                    complaint.target_case = new_case
        else:
            return Response({"detail": "You do not have permission to review complaints."}, status=status.HTTP_403_FORBIDDEN)
        
        complaint.save()
        return Response(ComplaintSerializer(complaint).data)


class CrimeSceneReportViewSet(viewsets.ModelViewSet):
    serializer_class = CrimeSceneReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return CrimeSceneReport.objects.none()
            
        if self.request.user.access_level < 20:
            return CrimeSceneReport.objects.none()
            
        return CrimeSceneReport.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        
        if user.access_level < 20:
            raise PermissionDenied("Only officers can submit crime scene reports.")

        if user.access_level == 90:
            with transaction.atomic():
                report = serializer.save(
                    reporting_officer=user, 
                    status=CrimeSceneReport.Status.APPROVED,
                    reviewed_by=user,
                    review_notes="Auto-approved by Chief"
                )
                new_case = Case.objects.create(
                    title=f"Direct Case: Crime Scene #{report.id}",
                    description=f"{report.description}\nWitnesses: {report.witness_info}",
                    investigating_officer=user
                )
                report.related_case = new_case
                report.save()
        else:
            serializer.save(
                reporting_officer=user, 
                status=CrimeSceneReport.Status.PENDING_SUPERIOR
            )

    @extend_schema(request=CrimeSceneReviewSerializer, responses={200: CrimeSceneReportSerializer})
    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """Superior Officer Approval Logic"""
        report = self.get_object()
        user = request.user
        
        if user.access_level <= report.reporting_officer.access_level:
            return Response(
                {"detail": "Review must be conducted by a superior officer with a higher rank."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if report.status != CrimeSceneReport.Status.PENDING_SUPERIOR:
            return Response({"detail": "This report is not pending review."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CrimeSceneReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        
        with transaction.atomic():
            report.reviewed_by = user
            report.review_notes = serializer.validated_data.get('review_notes', '')
            
            if action_type == 'approve':
                report.status = CrimeSceneReport.Status.APPROVED
                new_case = Case.objects.create(
                    title=f"Case from Crime Scene #{report.id}",
                    description=f"{report.description}\nWitnesses: {report.witness_info}",
                    investigating_officer=user
                )
                report.related_case = new_case
            elif action_type == 'reject':
                report.status = CrimeSceneReport.Status.REJECTED
            
            report.save()
            
        return Response(CrimeSceneReportSerializer(report).data)


class CaseViewSet(viewsets.ModelViewSet):
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Case.objects.none()

        user = self.request.user
        
        if user.access_level == 0:
            return Case.objects.filter(complainants=user)
        else:
            return Case.objects.all()
