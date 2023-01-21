from django import template

from minutes.models import Meeting

register = template.Library()


@register.simple_tag
def latest_minutes():
    return Meeting.objects.latest("date")
