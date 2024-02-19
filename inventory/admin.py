from django.contrib import admin

from .models import Inventory, Loan, Record, Suggestion


class InventoryAdmin(admin.ModelAdmin):
    list_display = ("name", "suggestions", "loans")
    list_filter = ("suggestions", "loans")


class LoanAdmin(admin.ModelAdmin):
    model = Loan
    list_display = ("requester", "start_date",
                    "end_date", "state_text", "inventory")
    list_filter = ("inventory",)
    fields = ("requester", "inventory", "items", "start_date", "end_date", "authorised", "rejected", "taken_when",
              "taken_who", "returned_when", "returned_who", "notes", "state_text")
    readonly_fields = ('state_text', "start_date", "end_date", "authorised", "rejected", "taken_when",
                       "taken_who", "returned_when", "returned_who")


class RecordAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "quantity", "owner", "inventory")
    list_filter = ("inventory",)
    autocomplete_fields = ("owner",)


class SuggestionAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "archived", "inventory")
    list_filter = ("inventory", "archived")


# Register your models here.
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Record, RecordAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
admin.site.register(Loan, LoanAdmin)
