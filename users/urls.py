from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [

    path('user/edit/', views.Edit.as_view(), name='edit'),

    path('user/<int:pk>/', views.ProfileView.as_view(), name='user'),
    path('user/me/', views.MyProfile.as_view(), name='me'),

    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),

    path('signup/', views.Signup.as_view(), name='signup'),

    path('membership/verify/', views.VerifyRequest.as_view(), name='verifyrequest'),
    path('membership/verify-confirm/',
         views.VerifyConfirm.as_view(), name='verifyconfirm'),

    path('change-password/',
         views.ChangePassword.as_view(),
         name='password_change'),

    path('reset-password/',
         views.PasswordReset.as_view(),
         name='password_reset'),

    path('reset-password/done/',
         auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),

    path('reset-password/<slug:uidb64>/<slug:token>',
         views.PasswordResetConfirm.as_view(),
         name='password_reset_confirm'),

    path('user/<int:pk>/achievements/',
         views.AllAchievements.as_view(),
         name='user_achievements'),
    path('user/me/achievements/',
         views.MyAchievements.as_view(),
         name='my_achievements'),

    path('tutorial/', views.Tutorial.as_view(), name='tutorial'),
    path('tutorial-done/', views.TutorialDone.as_view(), name='tutorial_done'),

    # API stuff
    path('user/allmembers/', views.allmembers, name='allmembers'),
]
