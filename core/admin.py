from django.contrib import admin
from .models import Task, UserProfile

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'status', 'business', 'created_at']
    list_filter = ['status', 'created_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']

