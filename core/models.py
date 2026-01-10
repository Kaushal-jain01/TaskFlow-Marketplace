from django.db import models
from django.contrib.auth.models import User
import uuid

# UserProfile extends Django's built-in User model to store application-specific
# information such as role (business/worker), phone number, and address.
# Each user has exactly one profile (OneToOne relationship), and the profile
# is automatically deleted when the user is deleted.
class UserProfile(models.Model):
    ROLE_CHOICES = [('business', 'Business'), ('worker', 'Worker')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
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
    business = models.ForeignKey(User, related_name='posted_tasks', on_delete=models.CASCADE)
    worker = models.ForeignKey(User, null=True, blank=True, related_name='claimed_tasks', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    proof_image = models.ImageField(upload_to='proofs/', blank=True, null=True)
    duration_minutes = models.IntegerField(default=15)
    created_at = models.DateTimeField(auto_now_add=True)


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
    is_paid = models.BooleanField(default=False) 
    
    def __str__(self):
        return f"Payment {self.id} for Task {self.task.id}"