from django.db import models
from django.contrib.auth.models import User

# extension to django's User class which has authentication details
# as well as some basic info such as name
class Member(models.Model):
	equiv_user = models.OneToOneField(User, on_delete=models.PROTECT)
	def __str__(self):
		return self.equiv_user.username
	bio = models.CharField(max_length=4096, blank=True)
	signature = models.CharField(max_length = 1024, blank=True)

	# Sends message to a user
	# Utility method
	def direct_message(self, other):
		pass
