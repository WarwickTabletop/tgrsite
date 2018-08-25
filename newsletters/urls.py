from django.urls import path
from django.shortcuts import render
from django.views.generic import TemplateView
from . import views

urlpatterns = [
	path('', views.Index.as_view(template_name='newsletters/index.html'), name='newsletters_index'),
	path('create', views.Create.as_view(template_name='newsletters/create.html'), name='newsletters_create'),
	path('<int:pk>', views.Detail.as_view(template_name='newsletters/detail.html'), name='newsletters_detail'),
]

