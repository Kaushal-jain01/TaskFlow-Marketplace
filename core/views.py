from django.shortcuts import get_object_or_404
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
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
        return Task.objects.filter(
            models.Q(status='open') |
            models.Q(created_by=user) |
            models.Q(claimed_by=user)
        ).order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================
# TASK DETAIL
# ============================
class TaskDetailView(generics.RetrieveAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()


# ============================
# CLAIM TASK
# ============================
class ClaimTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk, status='open')

        if task.created_by == request.user:
            return Response(
                {"error": "You cannot claim your own task"},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.claimed_by = request.user
        task.status = 'claimed'
        task.save()

        return Response({
            "message": "✅ Task claimed successfully",
            "task": TaskSerializer(task).data
        })


# ============================
# COMPLETE TASK (UPLOAD PROOF)
# ============================
class CompleteTaskView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, pk):
        task = get_object_or_404(
            Task,
            pk=pk,
            claimed_by=request.user,
            status='claimed'
        )

        if 'proof_image' in request.data:
            task.proof_image = request.data['proof_image']

        task.status = 'completed'
        task.updated_at = timezone.now()
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

    def post(self, request, pk):
        task = get_object_or_404(
            Task,
            pk=pk,
            created_by=request.user,
            status='completed'
        )

        task.status = 'approved'
        task.updated_at = timezone.now()
        task.save()

        return Response({"message": "✅ Task approved"})


# ============================
# PAY TASK (STRIPE)
# ============================
class PayTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        task = get_object_or_404(
            Task,
            pk=pk,
            created_by=request.user,
            status='approved'
        )

        intent = stripe.PaymentIntent.create(
            amount=int(task.price * 100),
            currency="inr",
            description=f"Payment for task {task.title}",
            automatic_payment_methods={"enabled": True},
        )

        Payment.objects.create(
            task=task,
            stripe_payment_intent_id=intent.id,
            amount=task.price,
            status="pending",
        )

        return Response({"client_secret": intent.client_secret})


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
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class PublicProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile


# ============================
# USERS (OPTIONAL)
# ============================
class GetAllUsers(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    queryset = User.objects.all()
