from django import template
from django.utils.safestring import mark_safe

from website_settings import models

register = template.Library()


@register.simple_tag
def string_setting(key):
    obj, new = models.StringProperty.objects.get_or_create(
        key__iexact=key, defaults={"key": key.lower(), "value": ""})
    res = obj.value
    return mark_safe(res)


@register.simple_tag
def text_setting(key):
    obj, new = models.TextProperty.objects.get_or_create(
        key__iexact=key, defaults={"key": key.lower(), "value": ""})
    res = obj.value
    return mark_safe(res)
