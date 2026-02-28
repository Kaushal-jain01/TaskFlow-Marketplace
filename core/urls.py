from django.urls import path
from core.views import *
from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [

    # HEALTH CHECK
    path("health/", HealthCheckView.as_view(), name="health-check"),

    # AUTH / PROFILE
    path("auth/register/", RegisterView.as_view(), name="register"),
    path('auth/token/', TokenObtainPairView.as_view(), name='token'),
    
    path("auth/profile/", ProfileView.as_view(), name="profile"),
    path("auth/profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("auth/profile/<str:username>/", PublicProfileView.as_view(), name="public-profile"),

    # TASKS
    path("tasks/", TaskListCreateView.as_view(), name="task-list-create"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),

    # Actions
    path("tasks/<int:pk>/claim/", ClaimTaskView.as_view(), name="task-claim"),
    path("tasks/<int:pk>/complete/", CompleteTaskView.as_view(), name="task-complete"),
    path("tasks/<int:pk>/approve/", ApproveTaskView.as_view(), name="task-approve"),
    path("tasks/<int:pk>/pay/", PayTaskView.as_view(), name="task-pay"),

    # Discussion
    path("tasks/<int:pk>/comments/", TaskCommentListCreateView.as_view(), name="task-comments"),

    # STRIPE WEBHOOK
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),

    # NOTIFICATIONS
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/<int:pk>/read/", MarkNotificationReadView.as_view(), name="notification-read"),

    # USERS (ADMIN ONLY)
    path("users/", GetAllUsers.as_view(), name="all-users"),

    # Dashboard Stats
    path("dashboard/business/", business_dashboard_view),
    path("dashboard/worker/", worker_dashboard_view),
]
