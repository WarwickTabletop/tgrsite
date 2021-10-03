from django.contrib import admin

from .models import Rpg, Tag


class RpgAdmin(admin.ModelAdmin):
    autocomplete_fields = ('game_masters', 'members', 'tags')
    fieldsets = (
        (None, {
            'fields': ['title', 'system', 'description', 'timeslot', 'location', 'players_wanted', 'finishes',
                       'is_in_the_past', 'tags']}),
        ("Users", {'fields': ['creator', 'game_masters', 'members', 'messaging_thread']}),
        ("Admin", {'fields': ['pinned', 'unlisted', 'discord', 'member_only', 'published', 'parent',
                              'child_signup_only', 'success_message']}),
    )


class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)


admin.site.register(Rpg, RpgAdmin)
admin.site.register(Tag, TagAdmin)
