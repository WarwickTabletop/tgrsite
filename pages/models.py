from django.db import models
from django.shortcuts import reverse

from users.models import Achievement


class Page(models.Model):
    class Permissions(models.IntegerChoices):
        PUBLIC = 0, 'Public'
        USER = 1, 'Logged In'
        MEMBER = 2, 'Member'
        EX_EXEC = 3, 'Ex-Exec'
        EXEC = 4, 'Exec'

    name = models.CharField(max_length=64, blank=False, help_text='Internal name of page')
    title = models.CharField(max_length=64, blank=True, help_text='Page title to display in titlebar of browser/tab')
    page_title = models.CharField(max_length=64, blank=True, help_text='Title to appear at the top of the page')
    breadcrumb_child = models.CharField(max_length=64, blank=True, help_text='Child element of the breadcrumb list')
    body = models.TextField(max_length=65536, blank=True, help_text='Page contents')
    head = models.TextField(max_length=16384, blank=True, help_text='Custom HTML to go in the <head> of the page')
    css = models.TextField(max_length=16384, blank=True, help_text='Custom CSS styles for the page')
    leftbar = models.TextField(max_length=16384, blank=True, help_text='Left sidebar contents (use cards)')
    markdown = models.BooleanField(default=True, help_text='Enable markdown rendering in this page')
    permission = models.IntegerField(choices=Permissions.choices, default=Permissions.PUBLIC)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, null=True, blank=True, default=None)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("page", kwargs={"name": self.name})


class BreadcrumbParents(models.Model):
    url = models.CharField(max_length=2048, blank=False, help_text='URL of parent')
    name = models.CharField(max_length=64, blank=False, help_text='Name to display')
    order = models.IntegerField(blank=False, help_text='Order parents are to appear (lower is earlier)')
    page = models.ForeignKey(Page, blank=False, on_delete=models.CASCADE, related_name="breadcrumb_parents")

    class Meta:
        verbose_name = "Breadcrumb Parent"
        verbose_name_plural = "Breadcrumb Parents"


class Widget(models.Model):
    POSTER = 0
    EVENTS = 1
    WIDGETS = ((POSTER, "Event Poster"), (EVENTS, "Upcoming Events"))
    type = models.SmallIntegerField(choices=WIDGETS, help_text='Add sidebar widgets you want to appear on this page')
    page = models.ForeignKey(Page, blank=False, on_delete=models.CASCADE, related_name="widgets")
    wide = models.BooleanField(default=False,
                               help_text='Set this to true if the widget should'
                                         ' only appear while the sidebar is separate')

    def __str__(self):
        t = self.type
        for i in self.WIDGETS:
            if t == i[0]:
                return i[1]
        else:
            return "Unknown"
