from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.timezone import now

from users import models as users


# Create your models here.
class Folder(models.Model):
    name = models.CharField(max_length=30,
                            help_text="Letters, numbers or underscores only",
                            validators=[RegexValidator("^[a-zA-Z0-9\.][a-zA-Z0-9-_]*$",
                                                       "This may only contain letters, numbers or underscores")])
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    class Meta:
        unique_together = ('name', 'parent')
        ordering = ('-name',)

    def __str__(self):
        if self.parent is None:
            return "\\" + self.name + "\\"
        return str(self.parent) + self.name + "\\"

    @property
    def pretty_name(self):
        return self.name.replace("_", " ").replace(".", "")

    def parents(self):
        if self.parent is None:
            return [self.name]
        p = self.parent.parents()
        p.append(self.name)
        return p

    def parents_id(self):
        if self.parent is None:
            return [self.id]
        p = self.parent.parents_id()
        p.append(self.id)
        return p

    @classmethod
    def roots(cls):
        return cls.objects.filter(parent__isnull=True)

    def canonical_(self):
        return ("/".join(self.parents())).lower()


class Meeting(models.Model):
    name = models.CharField(max_length=30,
                            help_text="This is the name that appears in the URL - week_n is a sensible example. Letters, numbers or underscores only",
                            validators=[RegexValidator("^[a-zA-Z0-9][a-zA-Z0-9-_]*$",
                                                       "This may only contain letters, numbers or underscores")])
    title = models.CharField(max_length=80)
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, related_name="meetings")
    body = models.TextField()
    date = models.DateField(default=now)
    author = models.ForeignKey(users.Member, on_delete=models.PROTECT)

    class Meta:
        ordering = ("-date", "-name")
        unique_together = ("name", "folder")

    @property
    def pretty_name(self):
        return self.name.replace("_", " ")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("minutes:meeting_detail", kwargs={'folder': self.folder.canonical_(), 'name': self.name.lower()})
