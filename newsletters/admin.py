from django.contrib import admin
from .models import Newsletter

class NewsletterAdmin(admin.ModelAdmin):
    fields = ('title','body','author','pub_date','summary','ispublished','banner')
    autocomplete_fields = ('author',)

# Register your models here.
admin.site.register(Newsletter, NewsletterAdmin)
