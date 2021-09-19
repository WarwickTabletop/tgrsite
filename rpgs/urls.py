from django.urls import path

from . import views

app_name = "rpgs"

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('<int:pk>/', views.Detail.as_view(), name='detail'),

    path('create/', views.Create.as_view(), name='create'),
    path('<int:pk>/edit/', views.Update.as_view(), name='edit'),
    path('<int:pk>/delete/', views.Delete.as_view(), name='delete'),

    path('<int:pk>/join/', views.Join.as_view(), name='join'),
    path('<int:pk>/publish/', views.Publish.as_view(), name='publish'),
    path('<int:pk>/leave/', views.Leave.as_view(), name='leave'),

    path('<int:pk>/kick/', views.Kick.as_view(), name='kick'),
    path('<int:pk>/add_to/', views.AddMember.as_view(), name='add_to'),

    path('<int:pk>/message/', views.MessageGroup.as_view(), name='message'),

    path('api/alltags', views.alltags, name='all_tags')
]
