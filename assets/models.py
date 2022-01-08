from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


# Create your models here.
class Asset(models.Model):
    name = models.CharField(
        max_length=25, help_text="Enter a name to help recognise it.")
    assetFile = models.FileField(upload_to='assets/%Y/%m/%d/')

    def __str__(self):
        return self.name + ': ' + self.assetFile.url


# Create your models here.
class VisualAsset(models.Model):
    name = models.CharField(
        max_length=25, help_text="Enter a name to help recognise it.")
    lightAssetFile = models.FileField(
        upload_to='assets/themed/light/%Y/%m/%d/')
    darkAssetFile = models.FileField(
        upload_to='assets/themed/dark/%Y/%m/%d/', blank=True)

    def __str__(self):
        return self.name + ': ' + self.lightAssetFile.url

    def url(self, request):
        if self.darkAssetFile:
            if request.user.is_authenticated:
                if request.user.member.dark:
                    return self.darkAssetFile.url
        return self.lightAssetFile.url


# Delete the stored file when model is deleted
@receiver(post_delete, sender=Asset)
def submission_delete(sender, instance, **kwargs):
    instance.assetFile.delete(False)
