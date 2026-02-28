from django.shortcuts import get_object_or_404
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync


from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework.decorators import api_view, permission_classes

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

import stripe

from .models import *
from .serializers import *
from .services import *


stripe.api_key = settings.STRIPE_SECRET_KEY

# HEALTH CHECK
class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "awake"})


# TASK LIST + CREATE
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user # Get the logged-in user making the request
        queryset = Task.objects.all()

        status = self.request.query_params.get('status')
        if status == 'open':
            queryset = queryset.filter(status=status)

        type_filter = self.request.query_params.get('type')

        if type_filter == 'posted':
            queryset = queryset.filter(
                Q(created_by=user) & Q(status__in=['open'])
            )

        if type_filter == 'claimed':
            # Users claimed tasks that are NOT completed, approved, or paid
            queryset = queryset.filter(
                (Q(claimed_by=user) & ~Q(status__in=['completed', 'approved', 'paid']))
                | (Q(created_by=user) & Q(status__in=['claimed']))
            )

        elif type_filter == 'completed':
            # Tasks claimed by user that are completed
            queryset = queryset.filter(
                 (Q(claimed_by=user) & Q(status__in=['completed', 'approved']))
                | (Q(created_by=user) & Q(status__in=['completed', 'approved']))
            )

        elif type_filter == 'history':
            queryset = queryset.filter(
                Q(created_by=user) | Q(claimed_by=user),
                status__in=['paid']
            )

        return queryset.order_by('-updated_at')
    
    """
    perform_create() is a hook method that runs automatically when a new object is being created.
    It is called after serializer validation but before the object is finally saved.
    Internally, DRF does something like this:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)   # 👈 this is called
        return Response(serializer.data)
    """
    def perform_create(self, serializer):
        if self.request.user.userprofile.role != 'business':
            raise PermissionDenied("Only business users can create tasks.")

        task = serializer.save(created_by=self.request.user)
        invalidate_dashboard_cache(task)


# TASK DETAIL
class TaskDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = TaskDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(status='open') |
            Q(created_by=user) |
            Q(claimed_by=user)
        )
    
    # Why we need get_queyset() here?
    # If a user requests /tasks/7/:
    # Task 7 exists but is not in this filtered queryset
    # DRF returns 404 → user cannot see tasks they shouldn’t access

    # Without get_queryset():
    # DRF would try Task.objects.all() by default
    # Anyone could access any task by PK → security hole
    
    def perform_destroy(self, instance):
        # Why we need perform_destroy() here?
        # Even after get_queryset() filters accessible tasks, we still need
        # extra business rules for deletion:
        # 1️⃣ Only the creator of the task can delete it

        # 2️⃣ Only tasks with status 'open' can be deleted
        
        # After these checks pass, we can safely:
        # 3️⃣ Run extra logic (like cache invalidation)
        # 4️⃣ Delete the object instance from the database
        
        # So perform_destroy() is the **hook to enforce business rules and
        # perform custom actions when deleting a single object**.
        
        if instance.created_by != self.request.user:
            raise PermissionDenied("Only the task creator can delete this task")
        
        if instance.status != 'open':
            raise PermissionDenied("Only open tasks can be deleted")
        
        invalidate_dashboard_cache(instance)
        instance.delete()
            


# CLAIM TASK
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

        # Update task
        task.claimed_by = request.user
        task.status = 'claimed'
        task.save()

        create_notification(
            recipient=task.created_by,
            task=task,
            type='task_claimed',
            message=f"Task '{task.title}' has been claimed.",
            actor=request.user
        )
        invalidate_dashboard_cache(task)

        # SEND WEBSOCKET NOTIFICATION TO BUSINESS OWNER
        # channel_layer = get_channel_layer()

        # async_to_sync(channel_layer.group_send)(
        #     f"user_{task.created_by.id}",   # business owner's group
        #     {
        #         "type": "send_notification",
        #         "data": {
        #             "event": "TASK_CLAIMED",
        #             "task_id": task.id,
        #             "task_title": task.title,
        #             "claimed_by": request.user.username,
        #             "message": (
        #                 f"Your task '{task.title}' was claimed by "
        #                 f"{request.user.username}"
        #             )
        #         }
        #     }
        # )

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK
        )



# COMPLETE TASK (UPLOAD PROOF)
class CompleteTaskView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def patch(self, request, pk):
        task = get_object_or_404(
            Task.objects.all(),
            pk=pk,
            claimed_by=request.user,
            status='claimed'
        )

        if request.user.userprofile.role != 'worker':
            raise PermissionDenied("Only workers can complete tasks.")

        # Prevent double submission
        if hasattr(task, 'completion'):
            return Response(
                {"error": "Task already completed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate input
        proof_image = request.data.get('proof_image')
        completion_details = request.data.get('completion_details')

        if not proof_image or not completion_details:
            return Response(
                {"error": "Proof image and completion details are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add these 3 debug lines
        # from django.core.files.storage import default_storage
        # print("🎯 RENDER STORAGE:", default_storage.__class__.__name__)
        # print("🎯 SUPABASE_URL:", getattr(settings, 'SUPABASE_URL', 'MISSING'))
        # print("🎯 BUCKET:", getattr(settings, 'SUPABASE_BUCKET', 'MISSING'))

        # Create completion
        TaskCompletion.objects.create(
            task=task,
            completed_by=request.user,
            proof_image=proof_image,
            completion_details=completion_details
        )

        # Update task status
        task.status = 'completed'
        task.save()

        create_notification(
            recipient=task.created_by,
            task=task,
            type='task_completed',
            message=f"Task '{task.title}' has been completed.",
            actor=request.user
        )

        invalidate_dashboard_cache(task)

        return Response(
            {
                "message": "✅ Task marked as completed",
                "task_id": task.id
            },
            status=status.HTTP_200_OK
        )


# COMMENT ON TASK
class TaskCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['pk'])
        user = self.request.user

        if user != task.created_by and user != task.claimed_by:
            raise PermissionDenied("Not allowed to view comments")

        return task.comments.order_by('created_at')

    # This perform_create() method is called only after the serializer validates the incoming data for Comment. Once the data is validated, this method checks id the requested user is a Owner or Worker of the Task with the given pk. 
    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs['pk'])
        user = self.request.user

        if user != task.created_by and user != task.claimed_by:
            raise PermissionDenied("Not allowed to comment")

        serializer.save(task=task, user=user)



# APPROVE TASK
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

        create_notification(
            recipient=task.claimed_by,
            task=task,
            type='task_approved',
            message=f"Task '{task.title}' has been approved.",
            actor=request.user
        )

        invalidate_dashboard_cache(task)

        return Response({
            "message": "✅ Task approved",
            "task": TaskSerializer(task).data
        })



# PAY TASK (STRIPE)
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
            receipt_email=request.user.email, 
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
    

# STRIPE WEBHOOK
# This is called by Stripe after payment is completed. It verifies the webhook, updates payment and task status in DB, then sends a websocket notification to the worker about the payment.
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

        create_notification(
            recipient=task.claimed_by,
            task=task,
            type='task_paid',
            message=f"Task '{task.title}' has been paid.",
            actor=task.created_by
        )

        invalidate_dashboard_cache(task)

        print(f"✅ Task {task.id} PAID")

    return JsonResponse({"status": "success"})



# AUTH / PROFILE
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

    # RetrieveAPIView is designed to return one object only.
    # get_object() tells the view: “Which single database object should I return?”
    def get_object(self):
        return self.request.user.userprofile 
        # For the logged in user, it first fetches the related UserProfile object, then uses ProfileSerializer to convert that UserProfile instance into JSON data to send back in the API response.


class ProfileUpdateView(generics.UpdateAPIView):
    # generics.UpdateAPIView supports both PUT and PATCH by default
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

# Notifications
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by("-created_at")


# USERS (OPTIONAL)
class GetAllUsers(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()




# DASHBOARD STATS
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_dashboard_view(request):
    data = business_dashboard_stats(request.user.id)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def worker_dashboard_view(request):
    data = worker_dashboard_stats(request.user.id)
    return Response(data)

