from django.conf import settings
from django.db import models

# Create your models here.
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

from users.models import Achievement


class Redirect(models.Model):
    source = models.CharField(max_length=50)
    sink = models.CharField(max_length=1024)
    permanent = models.BooleanField(default=False)
    usages = models.PositiveIntegerField(
        default=0, help_text="The number of times that link has been used")
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, null=True, blank=True, default=None)

    def __str__(self):
        return self.source

    def get_absolute_url(self):
        return reverse("redirect", kwargs={"source": self.source})

    @property
    def url(self):
        try:
            url_ = settings.DEFAULT_PROTOCOL + settings.PRIMARY_HOST + self.get_absolute_url()
            return mark_safe('<a href="{}">{}</a>'.format(url_, url_))
        except NoReverseMatch:
            return "-"
