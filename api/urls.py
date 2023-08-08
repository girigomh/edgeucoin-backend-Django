from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import EmailTokenObtainPairView, ResetPasswordView, ProfileView, StudentView, ParentView, UserView, TeacherView, SignUpView, AuthCheck, SchoolView, RewardView

urlpatterns = [
    path("auth/", AuthCheck.as_view(), name='auth_check'),
    path('signup/', SignUpView.as_view(), name='token_obtain_pair'),
    path('reset/', ResetPasswordView.as_view(), name='reset_password'),
    path('token/', EmailTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', UserView.as_view(), name='user'),
    path("school/", SchoolView.as_view(), name='school'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('teacher/', TeacherView.as_view(), name='teacher'),
    path('student/', StudentView.as_view(), name='student'),
    path('parent/', ParentView.as_view(), name="parent"),
    path('reward/', RewardView.as_view(), name='reward')
]