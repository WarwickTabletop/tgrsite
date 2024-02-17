from django.contrib import admin
from .models import Newsletter

class NewsletterAdmin(admin.ModelAdmin):
    fields = ('title','body','author','summary','banner','ispublished','pub_date')
    readonly_fields = ('pub_date',)
    autocomplete_fields = ('author',)

# Register your models here.
admin.site.register(Newsletter, NewsletterAdmin)
