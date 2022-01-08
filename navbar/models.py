from django.db import models
from django.core import validators
from .validators import LocalableURLField


# Create your models here.
class Nav(models.Model):
    sort_index = models.IntegerField(default=0)
    text = models.CharField(max_length=15)
    icon = models.CharField(max_length=50,
                            validators=(validators.RegexValidator("^fa-", message="Please ensure that the icon name "
                                                                                  "includes the fa- prefix"),
                                        validators.RegexValidator("^[a-z-]+$",
                                                                  message="Icon names should contain only lowercase "
                                                                          "and hyphens")),
                            help_text="The name of the icon to use (including the fa- prefix)")
    icon_set = models.CharField(max_length=3, choices=(("fas", "Solid Style (fas)"), ("fab", "Brands Style (fab)")),
                                help_text="The fontawesome icon set this logo is from. (Please don't use Regular "
                                          "Style (far) icons: keep the style consistent)")

    class Meta:
        abstract = True
        ordering = ('sort_index',)

    def __str__(self):
        return self.text


class BarItem(Nav):
    target = LocalableURLField(
        blank=True, help_text="The url this menu item should lead to.")


class BarDropdown(Nav):
    pass


class DropDownItem(Nav):
    parent = models.ForeignKey(
        BarDropdown, on_delete=models.CASCADE, related_name="children")
    target = LocalableURLField(
        blank=True, help_text="The url this menu item should lead to.")
