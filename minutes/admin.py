# Register your models here.
from django.contrib import admin

from .models import Folder, Meeting


class FolderAdmin(admin.ModelAdmin):
    list_filter = ("parent",)


class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "folder")
    list_filter = ("folder",)
    autocomplete_fields = ("author",)


admin.site.register(Folder, FolderAdmin)
admin.site.register(Meeting, MeetingAdmin)
