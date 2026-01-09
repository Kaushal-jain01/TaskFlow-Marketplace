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
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from core.views import *

urlpatterns = [
    path('admin/', admin.site.urls),

    # Tasks 
    path('api/tasks/', TaskListCreateView.as_view(), name='task-list'),
    path('api/tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),

    # Authenticatiion
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token'),

    # Registration
    path('api/register/', RegisterView.as_view(), name='register'),

    # Profile view & update (private only)
    path('api/profile/', ProfileView.as_view(), name='profile'),
    path('api/profile/update/', ProfileUpdateView.as_view(), name='profile-update'),

    # Public profile view
    path('api/users/<str:username>/', PublicProfileView.as_view(), name='public-profile'),

    # Role-based task views 
    path('api/business-tasks/', BusinessTasksView.as_view(), name='business-tasks'),
    path('api/worker-tasks/', WorkerTasksView.as_view(), name='worker-tasks'),

    # Claiming & Completing tasks by Workers
    path('api/tasks/<int:pk>/claim/', ClaimTaskView.as_view(), name='claim-task'),
    path('api/tasks/<int:pk>/complete/', CompleteTaskView.as_view(), name='complete-task'),

]
