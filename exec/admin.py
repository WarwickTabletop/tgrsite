from django.contrib import admin

from .models import ExecRole

class ExecRoleAdmin(admin.ModelAdmin):
    fields = ("role_title","sort_index","incumbent","bio","responsibilities")
    autocomplete_fields = ("incumbent",)
    list_display = ("role_title","incumbent")

admin.site.register(ExecRole, ExecRoleAdmin)
