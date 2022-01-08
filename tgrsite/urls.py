from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from redirect.views import redirect

urlpatterns = [
    path('timetable/', include('timetable.urls')),
    path('admin/', admin.site.urls),
    path('forum/', include('forum.urls')),
    path('events/', include('rpgs.urls'), name='rpgs_root'),
    path('exec/', include('exec.urls')),
    path('', include('users.urls')),
    path('messages/', include('messaging.urls')),
    path('api/', include('templatetags.urls')),
    path('votes/', include('votes.urls')),
    path('newsletters/', include('newsletters.urls')),
    path('notifications/', include('notifications.urls')),
    path('inventory/', include('inventory.urls')),
    path('minutes/', include('minutes.urls')),
    path('gallery/', include('gallery.urls')),
    path('', include('pages.urls')),
    path('<path:source>/', redirect, name="redirect")
] + static(settings.MEDIA_URL,
           document_root=settings.MEDIA_ROOT)  # This only runs if DEBUG=True. Its a bad idea on prod

if settings.DEBUG:
    from django.views.generic import TemplateView

    print("debug urls added")
    urlpatterns += [
        path('400', TemplateView.as_view(template_name='400.html')),
        path('403', TemplateView.as_view(template_name='403.html')),
        path('404', TemplateView.as_view(template_name='404.html')),
        path('500', TemplateView.as_view(template_name='500.html')),
        path('test', TemplateView.as_view(template_name='test.html')),

    ]
    if settings.DEBUG_TOOLBAR:
        try:
            import debug_toolbar

            urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
        except ModuleNotFoundError:
            pass
