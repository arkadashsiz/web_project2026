from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Evidence, Testimony, Biological, Vehicle, IDDocument
from .serializers import (
    TestimonySerializer, BiologicalSerializer, 
    VehicleSerializer, IDDocumentSerializer
)
from .permissions import IsEvidenceActive, IsCollectorOrCaseLead, IsWitnessOwner

class BaseEvidenceViewSet(viewsets.ModelViewSet):
    """
    A core ViewSet that handles the automatic assignment of the collector,
    the evidence type, and protects queries based on police hierarchy.
    """
    permission_classes = [permissions.IsAuthenticated, IsEvidenceActive, IsCollectorOrCaseLead]
    
    # These must be defined in child classes
    evidence_model = None
    evidence_type = None

    def get_queryset(self):
        # 1. Protect Swagger schema generation from crashing
        if getattr(self, "swagger_fake_view", False):
            return self.evidence_model.objects.none()

        user = self.request.user
        
        # 2. Civilians (Level 0) and Cadets (Level 10) cannot view forensic/vehicle/ID evidence
        if user.access_level < 20:
            return self.evidence_model.objects.none()
            
        # 3. Police Officers (Level 20+) can see the evidence
        return self.evidence_model.objects.all()

    def perform_create(self, serializer):
        # Only Officers+ can collect and record evidence into the system
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
    
    # We add IsWitnessOwner specifically for testimonies
    permission_classes = BaseEvidenceViewSet.permission_classes + [IsWitnessOwner]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Testimony.objects.none()

        user = self.request.user
        
        # Civilians (0) can ONLY see testimonies where they are recorded as the witness
        if user.access_level == 0:
            return Testimony.objects.filter(witness=user)
            
        # Cadets cannot access, Officers+ can access all
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
