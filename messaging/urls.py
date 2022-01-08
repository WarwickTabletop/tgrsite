from django.urls import path

from . import views

app_name = "message"

urlpatterns = [
    path('', views.Index.as_view(), name='message_list'),
    path('new/', views.CreateGroup.as_view(), name='create_group'),
    path('thread/<int:pk>/', views.Thread.as_view(), name='message_thread'),
    path('thread/<int:thread>/full/',
         views.FullThread.as_view(), name='message_thread_full'),
    path('thread/name/', views.rename_thread, name='rename_thread'),
    path('dm_thread/<int:recipient>/',
         views.DMThread.as_view(), name='get_dm_thread'),
    path('reports/', views.Reports.as_view(), name='pending_reports'),
    path('control/delete/', views.DeleteView.as_view(), name='delete_message'),
    path('control/report/', views.ReportView.as_view(), name='report_message'),
    path('control/resolve/', views.ResolveView.as_view(), name='resolve_report'),
]
