from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path('', views.AllNotifications.as_view(), name='all_notifications'),
    path('clear/', views.ReadAll.as_view(), name='clear_notifications'),
    path('read/<int:pk>/', views.ReadNotification.as_view(),
         name='read_notification'),
    path('preferences/', views.UpdateSubscriptions.as_view(),
         name='notification_settings'),
    path('temp/', views.email_notifications),
    path('newsletter_subscribe/', views.QuickNewsletterSubscribe.as_view(),
         name='quick_newsletter_subscribe'),
]
