from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Evidence, Testimony, Biological, Vehicle, IDDocument
from .serializers import (
    TestimonySerializer, BiologicalSerializer,
    VehicleSerializer, IDDocumentSerializer
)
from .permissions import IsEvidenceActive, IsCollectorOrCaseLead, IsWitnessOwner


class BaseEvidenceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEvidenceActive, IsCollectorOrCaseLead]

    evidence_model = None
    evidence_type = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.evidence_model.objects.none()

        user = self.request.user

        if user.access_level < 20:
            return self.evidence_model.objects.none()

        return self.evidence_model.objects.all()

    def perform_create(self, serializer):
        if self.request.user.access_level < 20:
            raise PermissionDenied("Only authorized police personnel can record evidence.")

        serializer.save(
            collected_by=self.request.user,
            evidence_type=self.evidence_type
        )


class TestimonyViewSet(BaseEvidenceViewSet):
    serializer_class = TestimonySerializer
    evidence_model = Testimony
    evidence_type = Evidence.EvidenceType.TESTIMONY
    permission_classes = BaseEvidenceViewSet.permission_classes + [IsWitnessOwner]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Testimony.objects.none()

        user = self.request.user

        if user.access_level == 0:
            return Testimony.objects.filter(witness=user)

        if user.access_level >= 20:
            return Testimony.objects.all()

        return Testimony.objects.none()


class BiologicalViewSet(BaseEvidenceViewSet):
    serializer_class = BiologicalSerializer
    evidence_model = Biological
    evidence_type = Evidence.EvidenceType.BIOLOGICAL


class VehicleViewSet(BaseEvidenceViewSet):
    serializer_class = VehicleSerializer
    evidence_model = Vehicle
    evidence_type = Evidence.EvidenceType.VEHICLE


class IDDocumentViewSet(BaseEvidenceViewSet):
    serializer_class = IDDocumentSerializer
    evidence_model = IDDocument
    evidence_type = Evidence.EvidenceType.ID_DOCUMENT


from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .models import WitnessStatement
from .serializers import WitnessStatementSerializer
from .permissions import IsOwnerOrPolice
from evidence.models import Testimony, Evidence


class WitnessStatementViewSet(viewsets.ModelViewSet):
    serializer_class = WitnessStatementSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrPolice]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "access_level", 0) >= 20:
            return WitnessStatement.objects.all()
        return WitnessStatement.objects.filter(submitted_by=user)

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        user = request.user
        if getattr(user, "access_level", 0) < 20:
            return Response({"detail": "Only police can approve statements."}, status=403)

        statement = self.get_object()

        if statement.status != WitnessStatement.Status.PENDING:
            return Response({"detail": "This statement is already reviewed."}, status=400)

        with transaction.atomic():
            statement.status = WitnessStatement.Status.APPROVED
            statement.reviewed_by = user
            statement.reviewed_at = timezone.now()
            statement.review_note = request.data.get("review_note", "")
            statement.save()

            Testimony.objects.create(
                case=statement.case,
                title="Witness Testimony",
                description="Converted from witness statement",
                witness=statement.submitted_by,
                transcription=statement.statement,
                media_file=statement.media_file,
                collected_by=user,
                evidence_type=Evidence.EvidenceType.TESTIMONY
            )

        return Response({"detail": "Statement approved and testimony evidence created."}, status=200)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        user = request.user
        if getattr(user, "access_level", 0) < 20:
            return Response({"detail": "Only police can reject statements."}, status=403)

        statement = self.get_object()

        if statement.status != WitnessStatement.Status.PENDING:
            return Response({"detail": "This statement is already reviewed."}, status=400)

        statement.status = WitnessStatement.Status.REJECTED
        statement.reviewed_by = user
        statement.reviewed_at = timezone.now()
        statement.review_note = request.data.get("review_note", "")
        statement.save()

        return Response({"detail": "Statement rejected."}, status=200)
