from django.core.cache import cache
from .models import Task, User, Notification
from django.db.models import Sum

def business_dashboard_stats(user_id):
    key = f"dashboard:business:{user_id}"
    data = cache.get(key)

    if data:
        return data

    user = User.objects.get(id=user_id)

    total_paid_amount = (
        Task.objects
        .filter(created_by=user, status="paid")
        .aggregate(total=Sum("price"))["total"] or 0
    )

    data = {
        "posted": Task.objects.filter(created_by=user).count(),

        "open": Task.objects.filter(created_by=user ,
                                       status__in=['open']
                                       ).count(),

        "claimed": Task.objects.filter(created_by=user ,
                                       status__in=['claimed']
                                       ).count(),

        "pending": Task.objects.filter(created_by=user ,
                                       status__in=['completed', 'approved']
                                       ).count(),
        
        "paid": Task.objects.filter(created_by=user ,
                                       status__in=['paid']
                                       ).count(),

        "total_paid_amount": total_paid_amount,
    }
    cache.set(key, data, 300)

    return data


def worker_dashboard_stats(user_id):
    key = f"dashboard:worker:{user_id}"
    data = cache.get(key)

    if data:
        return data
    
    user = User.objects.get(id=user_id)

    total_earnings = (
        Task.objects
        .filter(claimed_by=user, status="paid")
        .aggregate(total=Sum("price"))["total"] or 0
    )
    
    data = {
        "claimed": Task.objects.filter(claimed_by=user).count(),

        "completed": Task.objects.filter(claimed_by=user ,
                                        status__in=['completed', 'approved', 'paid']
                                        ).count(),

        "total_earnings": total_earnings,
    }
    cache.set(key, data, 300)

    return data


def invalidate_dashboard_cache(task):
    cache.delete(f"dashboard:business:{task.created_by_id}")
    if task.claimed_by_id:
        cache.delete(f"dashboard:worker:{task.claimed_by_id}")


def create_notification(recipient, task, type, message):
    Notification.objects.create(
        recipient=recipient,
        task=task,
        type=type,
        message=message
    )