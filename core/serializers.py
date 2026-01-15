from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, UserProfile, Payment


# -------------------------
# User
# -------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


# -------------------------
# Task
# -------------------------
class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    claimed_by = UserSerializer(read_only=True)
    proof_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Task
        fields = '__all__'

        # Backend-controlled fields
        read_only_fields = [
            'id',
            'created_by',
            'claimed_by',
            'status',
            'created_at',
            'updated_at',
        ]


# -------------------------
# User Profile (registration)
# -------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Used ONLY during registration
    """
    class Meta:
        model = UserProfile
        fields = ['phone', 'address']


# -------------------------
# Profile View / Update
# -------------------------
class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'phone', 'address']
        read_only_fields = ['user']


# -------------------------
# Registration
# -------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'profile']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        UserProfile.objects.create(user=user, **profile_data)
        return user


# -------------------------
# Payment
# -------------------------
class PaymentSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'stripe_payment_intent_id', 'created_at']
