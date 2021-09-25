from datetime import date

from django.core import validators
from django.db import models
from django.shortcuts import reverse


class GoogleCalender(models.Model):
    url = models.CharField(max_length=120,
                           help_text="Please ensure that it starts at the // (i.e. without the https: or webcal: part)")
    name = models.CharField(max_length=30)
    sort = models.IntegerField()

    def __str__(self):
        return self.name


# Create your models here.
class Week(models.Model):
    startDate = models.CharField(max_length=10)
    number = models.SmallIntegerField()
    year = models.PositiveSmallIntegerField(default=date.today().year,
                                            validators=[validators.MinValueValidator(2000, message="Invalid year")],
                                            help_text="Academic year (use greater year, i.e. 18/19 is 2019)")

    def __str__(self):
        return str(self.year) + " week " + str(self.number)

    class Meta:
        ordering = ['-year', 'number']

    def get_absolute_url(self):
        return reverse("timetable")


class Event(models.Model):
    description = models.CharField(max_length=20)
    date_time_line = models.CharField(max_length=20)
    sort_key = models.SmallIntegerField()

    def __str__(self):
        return str(self.description) + " : " + str(self.date_time_line)

    class Meta:
        ordering = ['sort_key']


class Booking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    room = models.CharField(max_length=100)

    def __str__(self):
        return str(self.week) + ": " + str(self.event)


class ColourScheme(models.Model):
    name = models.CharField(max_length=20, help_text="A description to help you identify it")
    html_code = models.CharField(max_length=7, help_text="Enter hexcode of colour to be used (include #)")
    light_text = models.BooleanField(default=False,
                                     help_text="Should the text used be a light colour (for dark colours)")

    def __str__(self):
        return str(self.name) + " (" + str(self.html_code) + ")"


class Timetable(models.Model):
    title = models.CharField(max_length=30)
    events = models.ManyToManyField(Event)
    weeks = models.ManyToManyField(Week)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=False)
    colour = models.ForeignKey(ColourScheme, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse("timetable:single_timetable", kwargs={"pk": self.pk})


class RoomLink(models.Model):
    url = models.CharField(max_length=120,
                           help_text="Link provided by interactive map")
    room = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.room


class SpecialEvent(models.Model):
    title = models.CharField(max_length=128)
    url = models.URLField(blank=True, max_length=200)
    room = models.CharField(blank=True, max_length=30)
    week = models.SmallIntegerField()
    display_date = models.CharField(max_length=60, help_text="The description of date and time to display")
    sort_date = models.DateField(help_text="The date to sort by, usually start date")
    hide_date = models.DateField(help_text="The date to hide this event after")
    poster = models.ImageField(blank=True, upload_to='posters/%Y/%m/%d/')

    def __str__(self):
        return self.title + ": " + self.display_date
