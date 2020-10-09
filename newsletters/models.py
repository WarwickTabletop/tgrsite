from django.db import models
from django.urls import reverse

from users.models import Member


class Newsletter(models.Model):
    BANNERS = (
        ("newsletter-banner.png", "Older"),
        ("images/newsletter_banner_2.png", "2019-20"),
        ("images/newsletter_banner_3.png", "2020-21"),
    )
    title = models.CharField(max_length=256)
    body = models.TextField()
    author = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True)
    pub_date = models.DateTimeField('Date Posted', auto_now_add=True)
    summary = models.CharField('Summary', max_length=256)
    ispublished = models.BooleanField('Is Published?')
    banner = models.CharField(max_length=255, choices=BANNERS, default=BANNERS[-1][0])

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('newsletters:newsletters_detail', kwargs={'pk': self.id})

    class Meta:
        permissions = (
            ("modify_others", "Can edit other newsletters"),
        )
