from django.shortcuts import HttpResponseRedirect, HttpResponsePermanentRedirect, get_object_or_404
from django.urls import reverse

from .models import Redirect
from users.achievements import give_this_achievement_once


# Create your views here.
def redirect(request, source):
    sink = get_object_or_404(Redirect, source__iexact=source)
    sink.usages += 1
    sink.save()
    if sink.achievement and not request.user.is_anonymous:
        give_this_achievement_once(
            request.user.member, sink.achievement, request=request)
    if sink.permanent:
        return HttpResponsePermanentRedirect(sink.sink)
    else:
        return HttpResponseRedirect(sink.sink)
