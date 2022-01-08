from django.db import models

from users.models import Member


class ExecRole(models.Model):
    sort_index = models.IntegerField(
        default=0, help_text='Index for sorting. Lower value = earlier in list.')
    role_title = models.CharField(max_length=48)
    bio = models.TextField(blank=True,
                           help_text='Description of the role and what it entails, as well as a short personal bio.')
    responsibilities = models.TextField(blank=True,
                                        help_text='Formal description of the requirements and duty of the role.')
    incumbent = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text='Member who is currently in this role', related_name="exec_roles")

    def __str__(self):
        return "{0} ({1})".format(self.role_title, str(self.incumbent))
