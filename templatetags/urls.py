from django.urls import path

from . import views

app_name = "utilities"

urlpatterns = [
    path('md_preview/', views.MarkdownPreview.as_view(), name='preview'),
    path('md_preview_safe/', views.MarkdownPreviewSafe.as_view(), name='preview_safe'),
    path('md_preview_newsletter/',
         views.MarkdownPreviewNewsletter.as_view(), name='preview_newsletter'),
    path('md_preview_text/', views.MarkdownPreviewText.as_view(), name='preview_text'),
]
