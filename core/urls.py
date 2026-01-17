from django.urls import path
from django.contrib import admin
from core.views import (
    TaskListCreateView,
    TaskDetailView,
    ClaimTaskView,
    CompleteTaskView,
    ApproveTaskView,
    PayTaskView,
    stripe_webhook,
    RegisterView,
    ProfileView,
    ProfileUpdateView,
    PublicProfileView,
    GetAllUsers,
)
from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [

    # ============================
    # AUTH / PROFILE
    # ============================
    path("auth/register/", RegisterView.as_view(), name="register"),
    path('auth/token/', TokenObtainPairView.as_view(), name='token'),
    
    path("auth/profile/", ProfileView.as_view(), name="profile"),
    path("auth/profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("auth/profile/<str:username>/", PublicProfileView.as_view(), name="public-profile"),

    # ============================
    # TASKS
    # ============================
    path("tasks/", TaskListCreateView.as_view(), name="task-list-create"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("tasks/<int:pk>/claim/", ClaimTaskView.as_view(), name="task-claim"),
    path("tasks/<int:pk>/complete/", CompleteTaskView.as_view(), name="task-complete"),
    path("tasks/<int:pk>/approve/", ApproveTaskView.as_view(), name="task-approve"),
    path("tasks/<int:pk>/pay/", PayTaskView.as_view(), name="task-pay"),

    # ============================
    # STRIPE WEBHOOK
    # ============================
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),


    # ============================
    # USERS (ADMIN ONLY)
    # ============================
    path("users/", GetAllUsers.as_view(), name="all-users"),
]
