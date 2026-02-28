from django.contrib import admin
from .models import Task, Payment, UserProfile


# TASK ADMIN
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'price',
        'status',
        'created_by',
        'claimed_by',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-updated_at',)



# PAYMENT ADMIN
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task',
        'amount',
        'status',
        'created_at',
    )
    list_filter = ('status',)
    search_fields = ('task__title',)



# USER PROFILE ADMIN
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone',
        'role'
    )
    search_fields = ('user__username', 'phone')
