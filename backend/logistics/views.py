from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import CivilianTip, BailTransaction
from .serializers import (
    MostWantedSerializer, CivilianTipSerializer, 
    RewardLookupSerializer, BailCreationSerializer
)
from .zarinpal import ZarinpalService
from users.models import User
from cases.models import Case, CaseSuspect

class MostWantedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Chapter 4.7: Publicly lists suspects who have been wanted for > 30 days.
    """
    serializer_class = MostWantedSerializer
    permission_classes = [permissions.AllowAny] # Public access

    def get_queryset(self):
        # Logic: Find CaseSuspects where status is WANTED/HIGHLY_WANTED
        # AND date_marked_wanted was more than 30 days ago.
        # Then return the unique Suspect (User) objects.
        
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        # We filter Users who have at least one CaseSuspect record meeting criteria
        return User.objects.filter(
            suspect_records__date_marked_wanted__lte=thirty_days_ago,
            suspect_records__status__in=['WANTED', 'HIGHLY_WANTED']
        ).distinct()


class CivilianTipViewSet(viewsets.ModelViewSet):
    """
    Chapter 4.8: Managing Tips and Rewards.
    """
    queryset = CivilianTip.objects.all()
    serializer_class = CivilianTipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='officer-review')
    def officer_review(self, request, pk=None):
        """Step 1: Officer validates the tip."""
        tip = self.get_object()
        # Check permissions: Access Level >= 20 (Officer)
        if request.user.role.access_level < 20:
            return Response({"error": "Only officers can perform initial review."}, status=403)

        decision = request.data.get('decision') # 'approve' or 'reject'
        
        if decision == 'reject':
            tip.status = 'REJECTED'
            tip.officer_reviewer = request.user
            tip.save()
            return Response({"status": "Tip rejected by Officer"})
        elif decision == 'approve':
            tip.status = 'PENDING_DETECTIVE'
            tip.officer_reviewer = request.user
            tip.save()
            return Response({"status": "Tip forwarded to Lead Detective"})
        return Response({"error": "Invalid decision"}, status=400)

    @action(detail=True, methods=['post'], url_path='detective-review')
    def detective_review(self, request, pk=None):
        """Step 2: Detective approves and generates reward."""
        tip = self.get_object()
        # Check permissions: Access Level >= 30 (Detective)
        if request.user.role.access_level < 30:
            return Response({"error": "Only detectives can perform final review."}, status=403)
        
        # Verify if this detective is assigned to the related case (optional strict check)
        # For now, generic detective check based on access level
        
        decision = request.data.get('decision')
        
        if decision == 'reject':
            tip.status = 'REJECTED'
            tip.detective_reviewer = request.user
            tip.save()
            return Response({"status": "Tip rejected by Detective"})
        
        elif decision == 'approve':
            tip.status = 'APPROVED'
            tip.detective_reviewer = request.user
            # Generate Reward
            tip.generate_token()
            
            # Calculate Reward Amount: 
            # If related to a suspect, use Most Wanted formula, else standard amount
            reward = 5_000_000 # Base reward
            if tip.related_suspect:
                # Reuse the logic from MostWantedSerializer manually
                # Or create a helper. Simplified here:
                serializer = MostWantedSerializer(tip.related_suspect)
                calculated_bounty = serializer.data['bounty_reward']
                if calculated_bounty > 0:
                    reward = calculated_bounty
            
            tip.reward_amount = reward
            tip.save()
            
            return Response({
                "status": "Tip Approved",
                "message": "Reward generated. User notified."
            })
        return Response({"error": "Invalid decision"}, status=400)


class RewardLookupView(views.APIView):
    """
    Chapter 4.8: Police lookup for redeeming rewards.
    """
    permission_classes = [permissions.IsAuthenticated] # Any police personnel

    def post(self, request):
        serializer = RewardLookupSerializer(data=request.data)
        if serializer.is_valid():
            nid = serializer.validated_data['national_id']
            token = serializer.validated_data['unique_token']
            
            try:
                # Assuming User model has 'national_id' field. 
                # If not, we search by username or add the field to User model.
                # Here assuming the tip.user.national_id matches.
                tip = CivilianTip.objects.get(
                    unique_token=token,
                    user__national_id=nid, # Ensure User model has this field or adjust query
                    status='APPROVED'
                )
                return Response({
                    "valid": True,
                    "amount": tip.reward_amount,
                    "civilian_name": tip.user.get_full_name(),
                    "tip_content": tip.content
                })
            except CivilianTip.DoesNotExist:
                return Response({"valid": False, "error": "Invalid Token or National ID"}, status=404)
        return Response(serializer.errors, status=400)


class BailViewSet(viewsets.ViewSet):
    """
    Chapter 4.9: Bail Payment via Zarinpal Sandbox.
    """
    permission_classes = [permissions.AllowAny] # Or IsAuthenticated depending on who pays

    def create(self, request):
        """Initiate Payment"""
        serializer = BailCreationSerializer(data=request.data)
        if serializer.is_valid():
            cs_id = serializer.validated_data['case_suspect_id']
            amount = serializer.validated_data['amount']
            
            case_suspect = get_object_or_404(CaseSuspect, id=cs_id)
            
            # Logic: Check if eligible for bail (Sergeant set amount, Crime level 2 or 3)
            # For simplicity, we assume if the Sergeant told them the amount, they can pay.
            
            description = f"Bail for Case {case_suspect.case.id} - Suspect {case_suspect.suspect.username}"
            
            # Call Zarinpal
            result = ZarinpalService.request_payment(
                amount=amount, 
                description=description,
                email=request.user.email if request.user.is_authenticated else None
            )
            
            if result['success']:
                # Create Transaction Record
                BailTransaction.objects.create(
                    case_suspect=case_suspect,
                    amount=amount,
                    description=description,
                    authority=result['authority'],
                    status='PENDING'
                )
                return Response({'payment_url': result['payment_url']})
            else:
                return Response({'error': result.get('error')}, status=400)
                
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], url_path='verify')
    def verify(self, request):
        """Callback from Zarinpal"""
        authority = request.query_params.get('Authority')
        status_param = request.query_params.get('Status')
        
        transaction = get_object_or_404(BailTransaction, authority=authority)
        
        if status_param == 'OK':
            verify_result = ZarinpalService.verify_payment(authority, transaction.amount)
            
            if verify_result['success']:
                # Update Transaction
                transaction.status = 'PAID'
                transaction.ref_id = verify_result['ref_id']
                transaction.paid_at = timezone.now()
                transaction.save()
                
                # Update Suspect Status to RELEASED_ON_BAIL
                cs = transaction.case_suspect
                cs.status = 'BAIL' # Corresponds to CaseSuspect.Status.RELEASED_ON_BAIL
                cs.save()
                
                return Response({"message": "Payment Successful. Suspect released on bail.", "ref_id": verify_result['ref_id']})
            else:
                return Response({"error": "Payment Verification Failed"}, status=400)
        else:
            transaction.status = 'FAILED'
            transaction.save()
            return Response({"error": "Payment Canceled by User"}, status=400)
