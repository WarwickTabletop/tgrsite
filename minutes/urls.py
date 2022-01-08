from django.urls import path

from . import views

app_name = "minutes"

urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.CreateMeeting.as_view(), name="new_meeting"),
    path("edit/<int:pk>/", views.UpdateMeeting.as_view(), name="change_meeting"),
    # Shortcut as pk is technically sufficient
    path("<int:pk>/", views.meetingBounce, name="meeting_bounce"),
    path("<path:folder>/<str:name>/",
         views.MeetingDetail.as_view(), name="meeting_detail"),
]
