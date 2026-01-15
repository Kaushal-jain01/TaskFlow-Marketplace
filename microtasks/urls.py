"""
URL configuration for microtasks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenObtainPairView

from core.views import (
    TaskListCreateView,
    TaskDetailView,
    ClaimTaskView,
    CompleteTaskView,
    ApproveTaskView,
    PayTaskView,
    RegisterView,
    ProfileView,
    ProfileUpdateView,
    PublicProfileView,
    GetAllUsers,
    stripe_webhook,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ============================
    # USERS (PUBLIC URL)
    # ============================
    path('api/all-users/', GetAllUsers.as_view(), name='get-all-users'),

    # ============================
    # AUTH
    # ============================
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token'),
    path('api/register/', RegisterView.as_view(), name='register'),

    # ============================
    # PROFILE
    # ============================
    path('api/profile/', ProfileView.as_view(), name='profile'),
    path('api/profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('api/users/<str:username>/', PublicProfileView.as_view(), name='public-profile'),

    # ============================
    # TASKS
    # ============================
    path('api/tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('api/tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),

    path('api/tasks/<int:pk>/claim/', ClaimTaskView.as_view(), name='claim-task'),
    path('api/tasks/<int:pk>/complete/', CompleteTaskView.as_view(), name='complete-task'),
    path('api/tasks/<int:pk>/approve/', ApproveTaskView.as_view(), name='approve-task'),
    path('api/tasks/<int:pk>/pay/', PayTaskView.as_view(), name='pay-task'),

    # ============================
    # STRIPE
    # ============================
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
