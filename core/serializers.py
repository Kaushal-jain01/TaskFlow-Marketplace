from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, UserProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TaskSerializer(serializers.ModelSerializer):
    business = UserSerializer(read_only=True)  # Show business details
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'status']
