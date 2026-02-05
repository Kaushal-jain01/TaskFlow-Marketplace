from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *


# User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


# Task
class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    claimed_by = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'price',
            'created_by',
            'claimed_by',
            'status',
            'duration_minutes',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_by',
            'claimed_by',
            'status',
            'created_at',
            'updated_at',
        ]


# Task Completion
class TaskCompletionSerializer(serializers.ModelSerializer):
    completed_by = UserSerializer(read_only=True)

    class Meta:
        model = TaskCompletion
        fields = [
            'id',
            'task',
            'completed_by',
            'proof_image',
            'completion_details',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'completed_by',
            'created_at',
        ]

# Task comment
class TaskCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = [
            'id',
            'user',
            'message',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'user',
            'created_at',
        ]


# Task Detail
class TaskDetailSerializer(TaskSerializer):
    completion = TaskCompletionSerializer(read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + [
            'completion',
            'comments',
        ]


# User Profile (registration)
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Used ONLY during registration
    """
    class Meta:
        model = UserProfile
        fields = [
            'role',
            'phone',
            'address_line1',
            'city',
            'country',
            'postal_code',
        ]


# Profile View / Update
class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user',
            'role',
            'phone',
            'address_line1',
            'city',
            'country',
            'postal_code',
            
        ]
        read_only_fields = ['user']


# Registration
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    profile = UserProfileSerializer() # This allows frontend to send nested profile 
                                      # data at the time of user registration.
                                      # profile in the serializer = virtual field

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'profile'] # profile in fields = tells DRF 
                                                              # to expect this key in input JSON

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        UserProfile.objects.create(user=user, **profile_data)
        return user


# Payment
class PaymentSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'task',
            'amount',
            'status',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'task',
            'amount',
            'status',
            'created_at',
        ]

