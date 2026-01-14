from django.shortcuts import render, get_object_or_404
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,  AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import *
from .serializers import *
from .models import UserProfile
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.http import JsonResponse
import stripe
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

stripe.api_key = settings.STRIPE_SECRET_KEY

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    
    def get_permissions(self):
        # BLOCK workers from POST, allow everyone to GET
        if self.request.method == 'POST':
            profile = UserProfile.objects.get(user=self.request.user)
            if profile.role != 'business':
                raise PermissionDenied("Only businesses can post tasks")
        return [IsAuthenticated()]
    
    def get_queryset(self):
        return Task.objects.filter(
            models.Q(status='open') | 
            models.Q(business=self.request.user)
        )
    
    def perform_create(self, serializer):
        serializer.save(business=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Here role is extracted only to show in the response message
            role = request.data['profile']['role']
            return Response({
                "message": f"User registered as {role.title()}!",
                "username": user.username
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    # get_object() tells DRF which single object to return.
    # Here, it always fetches (or creates) the profile of the logged-in user,
    # instead of using an ID from the URL.
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
    permission_classes = [AllowAny]  # Public!
    
    def get_object(self):
        username = self.kwargs['username']
        user = get_object_or_404(User, username=username)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile


class BusinessTasksView(generics.ListAPIView):
    """Business sees only THEIR posted tasks"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(business=self.request.user)
    

class WorkerTasksView(generics.ListAPIView):
    """Worker sees claimed tasks + open tasks"""
    serializer_class = TaskSerializer  
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        profile = UserProfile.objects.get(user=user)
        if profile.role == 'worker':
            return Task.objects.filter(
                models.Q(worker=user) | models.Q(status='open')
            )
        return Task.objects.none()
    
# WORKER: Only open tasks (status=open, not claimed by anyone)
class WorkerOpenTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(
            status='open'  # Only unclaimed tasks
        ).order_by('-created_at')

# WORKER: Only THEIR tasks (claimed, completed)
class WorkerMyTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(
            worker=self.request.user,  # Only THEIR tasks
            status__in=['claimed', 'completed', 'approved']
        ).order_by('-created_at')

# BUSINESS: THEIR posted tasks
class BusinessPostedTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(
            business=self.request.user  # Only THEIR tasks
        ).order_by('-created_at')

# BUSINESS: Tasks claimed by workers (they need to review)
class BusinessClaimedTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(
            business=self.request.user,
            status='claimed'
        ).order_by('-created_at')


class ClaimTaskView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk, status='open')
        
        # Check if worker has profile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if profile.role != 'worker':
            return Response({"error": "Only workers can claim tasks"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        task.worker = request.user
        task.status = 'claimed'
        task.save()
        
        return Response({
            "message": "Task claimed successfully!",
            "task": TaskSerializer(task).data
        })


class CompleteTaskView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk, worker=request.user)
        
        if task.status != 'claimed':
            return Response({"error": "Task must be claimed first"}, status=400)
        
        # Upload proof image
        if 'proof_image' in request.data:
            task.proof_image = request.data['proof_image']
        
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        return Response({
            "message": "✅ Task completed with proof! Waiting business review.",
            "task": TaskSerializer(task).data
        })

class ApproveTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, business=request.user, status="completed")

        # 1️⃣ Create customer
        customer = stripe.Customer.create(
            name=request.user.username,
            email=request.user.email,
            address={
                "line1": "Business Address",
                "city": "Mumbai",
                "state": "MH",
                "postal_code": "400001",
                "country": "IN",
            },
        )

        # 2️⃣ Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(task.price * 100),
            currency="inr",
            customer=customer.id,
            description=f"Service payment for task {task.title}",
            automatic_payment_methods={"enabled": True},
        )

        payment = Payment.objects.create(
            task=task,
            stripe_payment_intent_id=intent.id,
            amount=task.price,
            status="pending",
        )

        task.status = "approved"
        task.save()

        return Response({
            "client_secret": intent.client_secret
        })


# Webhook (Stripe calls this)
# core/views.py - REPLACE your stripe_webhook with this:
@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle successful payment
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # FIXED: Get payment by intent_id, not task_id
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent['id'])
        payment.status = 'paid'
        payment.save()
        
        task = payment.task
        task.status = 'paid'  # Use status instead of is_paid
        task.is_paid = True
        task.save()
        
        print(f"✅ Task {task.id} PAID: {task.title}")

    return JsonResponse({'status': 'success'}, status=200)


class GetAllUsers(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    queryset = User.objects.all()

# @api_view(['GET'])
# def stripe_success(request):
#     payment_intent_id = request.GET.get('payment_intent')
#     client_secret = request.GET.get('payment_intent_client_secret')
    
#     return Response({
#         'message': '✅ Payment Success!',
#         'payment_intent': payment_intent_id,
#         'client_secret': client_secret,
#         'status': 'completed'
#     }, status=status.HTTP_200_OK)