from django.conf import settings  # import the settings file
from operator import itemgetter

from forum.models import Thread, Response
from navbar.models import BarDropdown, BarItem


def add_debug(request):
    return {'DEBUG': settings.DEBUG}


def latestposts(request):
    return {
        'latestthreads': Thread.objects.order_by('-pub_date')[:5],
        'latestresponses': Response.objects.order_by('-pub_date')[:5],
    }


def mergednavbar(request):
    links = [{'sort': x.sort_index, 'element': x, 'drop': False}
             for x in BarItem.objects.all()]
    drops = [{'sort': x.sort_index, 'element': x, 'drop': True}
             for x in BarDropdown.objects.all()]
    return {
        'navbar': sorted(links + drops, key=itemgetter("sort"))
    }
