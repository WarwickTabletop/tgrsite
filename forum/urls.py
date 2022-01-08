from django.urls import path

from . import views

app_name = "forum"

urlpatterns = [
    path('', views.RootForum.as_view(), name='forum'),
    path('<int:forum>/', views.ViewSubforum.as_view(), name='subforum'),
    path('recent/', views.Recent.as_view(), name='recent'),

    path('thread/<int:thread>/', views.ViewThread.as_view(), name='viewthread'),

    path('thread/<int:pk>/delete/',
         views.DeleteThread.as_view(), name='thread_delete'),
    path('thread/<int:pk>/edit/', views.EditThread.as_view(), name='thread_edit'),
    path('api/thread_subscription/',
         views.ChangeSubscription.as_view(), name='thread_subscribe'),

    path('response/<int:pk>/delete/',
         views.DeleteResponse.as_view(), name='response_delete'),
    path('response/<int:pk>/edit/',
         views.EditResponse.as_view(), name='response_edit'),
]
