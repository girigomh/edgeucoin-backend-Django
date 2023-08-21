from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import routers

from .views import *

urlpatterns = [
    path("auth/", AuthCheck.as_view(), name='auth_check'),
    path('signup/', SignUpView.as_view(), name='token_obtain_pair'),
    path('reset/', ResetPasswordView.as_view(), name='reset_password'),
    path('token/', EmailTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', UserView.as_view(), name='users'),
    path("school/", SchoolView.as_view(), name='school'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('teacher/', TeacherView.as_view(), name='teacher'),
    path('student/', StudentView.as_view(), name='student'),
    path('parent/', ParentView.as_view(), name="parent"),
    path('reward/', RewardView.as_view(), name='reward'),
    path('goal/', GoalView.as_view(), name='goal'),
    path("goals/", GoalsView.as_view(), name='goals'),
    path("record/", RecordView.as_view(), name='record'),
    path("complete/", CompleteView.as_view(), name='complete')
]