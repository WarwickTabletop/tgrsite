from django.db import models


# Create your models here.
class IdempotencyToken(models.Model):
    token = models.UUIDField()
    created = models.DateTimeField(auto_now_add=True)
    redirect = models.CharField(max_length=2048, blank=True)
