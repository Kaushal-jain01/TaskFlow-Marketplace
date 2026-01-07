from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated,  AllowAny
from .models import Task
from .serializers import TaskSerializer

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    # permission_classes = [IsAuthenticated]

    # List = public (students browse), Create = authenticated (business posts)
    def get_permissions(self):
        if self.request.method == 'GET':  # Browsing
            return [AllowAny()]
        return [IsAuthenticated()]  # Posting
    
    def get_queryset(self):
        return Task.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(business=self.request.user)  # Auto-set poster

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()

