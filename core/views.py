from django.shortcuts import get_object_or_404
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

import stripe

from .models import Task, Payment, UserProfile
from .serializers import (
    TaskSerializer,
    RegisterSerializer,
    ProfileSerializer,
    UserSerializer,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


# ============================
# TASK LIST + CREATE
# ============================
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()

        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        type_filter = self.request.query_params.get('type')

        if type_filter == 'posted':
            queryset = queryset.filter(created_by=user)

        elif type_filter == 'claimed':
            queryset = queryset.filter(claimed_by=user)

        elif type_filter == 'history':
            queryset = queryset.filter(
                Q(created_by=user) | Q(claimed_by=user),
                status__in=['completed', 'approved', 'paid']
            )

        return queryset.order_by('-updated_at')

    def perform_create(self, serializer):
        if self.request.user.userprofile.role != 'business':
            raise PermissionDenied("Only business users can create tasks.")

        serializer.save(created_by=self.request.user)


# ============================
# TASK DETAIL
# ============================
class TaskDetailView(generics.RetrieveAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(status='open') |
            Q(created_by=user) |
            Q(claimed_by=user)
        )


# ============================
# CLAIM TASK
# ============================
class ClaimTaskView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, pk):
        task = get_object_or_404(
            Task.objects.select_for_update(),
            pk=pk,
            status='open'
        )

        # Role check
        if request.user.userprofile.role != 'worker':
            raise PermissionDenied("Only workers can claim tasks.")

        # Creator cannot claim own task
        if task.created_by == request.user:
            return Response(
                {"error": "You cannot claim your own task"},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.claimed_by = request.user
        task.status = 'claimed'
        task.save()

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK
        )

# ============================
# COMPLETE TASK (UPLOAD PROOF)
# ============================
class CompleteTaskView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def patch(self, request, pk):
        task = get_object_or_404(
            Task,
            pk=pk,
            claimed_by=request.user,
            status='claimed'
        )

        if request.user.userprofile.role != 'worker':
            raise PermissionDenied("Only workers can complete tasks.")

        if 'proof_image' in request.data:
            task.proof_image = request.data['proof_image']

        task.status = 'completed'
        task.save()

        return Response({
            "message": "✅ Task marked as completed",
            "task": TaskSerializer(task).data
        })

# ============================
# APPROVE TASK
# ============================
class ApproveTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        task = get_object_or_404(
            Task,
            pk=pk,
            created_by=request.user,
            status='completed'
        )

        # Optional: role enforcement
        if request.user.userprofile.role != 'business':
            raise PermissionDenied("Only business users can approve tasks.")

        task.status = 'approved'
        task.save()

        return Response({
            "message": "✅ Task approved",
            "task": TaskSerializer(task).data
        })


# ============================
# PAY TASK (STRIPE)
# ============================
class PayTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        # Fetch the task: only creator can pay for approved tasks
        task = get_object_or_404(
            Task,
            pk=pk,
            created_by=request.user,
            status='approved'
        )

        # Role check: only business can trigger payment
        if request.user.userprofile.role != 'business':
            raise PermissionDenied("Only business users can pay for tasks.")

        # Get business profile for billing details
        business_profile = request.user.userprofile

        # Create Stripe PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(task.price * 100),  # in smallest currency unit
            currency="inr",
            description=f"Payment for task {task.title}",
            automatic_payment_methods={"enabled": True},
        )

        # Record payment in DB (status pending)
        Payment.objects.create(
            task=task,
            stripe_payment_intent_id=intent.id,
            amount=task.price,
            status="pending",
        )

        # Return client_secret + billing details for frontend
        return Response({
            "client_secret": intent.client_secret,
            "billing_details": {
                "name": request.user.username,
                "address": {
                    "line1": business_profile.address_line1,
                    "city": business_profile.city,
                    "country": business_profile.country,
                    "postal_code": business_profile.postal_code,
                }
            }
        })
    
# ============================
# STRIPE WEBHOOK
# ============================
@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return JsonResponse({"error": "Invalid webhook"}, status=400)

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]

        payment = Payment.objects.get(
            stripe_payment_intent_id=intent["id"]
        )
        payment.status = "paid"
        payment.save()

        task = payment.task
        task.status = "paid"
        task.updated_at = timezone.now()
        task.save()

        print(f"✅ Task {task.id} PAID")

    return JsonResponse({"status": "success"})


# ============================
# AUTH / PROFILE
# ============================
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User registered successfully", "username": user.username},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.userprofile


class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.userprofile


class PublicProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return get_object_or_404(UserProfile, user=user)


# ============================
# USERS (OPTIONAL)
# ============================
class GetAllUsers(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
