from django import template

from newsletters.models import Newsletter

register = template.Library()


@register.simple_tag
def latest_newsletter():
    return Newsletter.objects.filter(ispublished=True).latest('pub_date')
