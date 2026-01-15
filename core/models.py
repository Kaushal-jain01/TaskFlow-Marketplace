from django.db import models
from django.contrib.auth.models import User
import uuid

# UserProfile extends Django's built-in User model to store
# additional application-specific information such as phone
# number and address.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(max_length=200, blank=True)

class Task(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'), 
        ('claimed', 'Claimed'), 
        ('completed', 'Completed'), 
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    created_by = models.ForeignKey(
        User, 
        related_name='tasks_created', 
        on_delete=models.CASCADE
    )

    claimed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name='tasks_claimed',
        on_delete=models.CASCADE
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    proof_image = models.ImageField(upload_to='proofs/', blank=True, null=True)
    duration_minutes = models.IntegerField(default=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='payments')
    stripe_payment_intent_id = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment {self.id} for Task {self.task.id}"