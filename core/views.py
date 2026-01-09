from django.shortcuts import render, get_object_or_404
from django.db import models
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,  AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Task
from .serializers import TaskSerializer, RegisterSerializer, ProfileSerializer
from .models import UserProfile


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
    
    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk, worker=request.user)
        
        task.status = 'completed'
        task.save()
        
        return Response({
            "message": "Task marked complete! Waiting for business approval.",
            "task": TaskSerializer(task).data
        })
