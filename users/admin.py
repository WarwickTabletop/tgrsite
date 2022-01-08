from functools import reduce

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from rpgs.models import Rpg
from .models import Member, Membership, VerificationRequest, Achievement, AchievementAward


def field_property(field_name, **kwargs):
    def _from_property(admin, obj=None):
        if not obj:
            return None
        rv = reduce(getattr, field_name.split("."), obj)
        return rv() if callable(rv) else rv

    for key, value in kwargs.items():
        setattr(_from_property, key, value)
    return _from_property


class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'member'
    readonly_fields = ('dark', 'is_soc_member')


class MembershipInline(admin.StackedInline):
    model = Membership


class AchievementAwardInline(admin.StackedInline):
    model = Membership
    extra = 0


class RpgInline(admin.TabularInline):
    model = Rpg
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (MemberInline,)
    save_on_top = True


class MemberAdmin(admin.ModelAdmin):
    inlines = (MembershipInline,)
    search_fields = ('equiv_user__username', 'discord',
                     'equiv_user__first_name', 'equiv_user__last_name',)
    readonly_fields = ('dark',)
    list_display = ('username', 'discord', 'firstname', 'last_name', 'pronoun')


class AchievementAwardAdmin(admin.ModelAdmin):
    list_display = ('member', 'achievement', 'achieved_at')
    list_filter = ('achievement',)
    autocomplete_fields = ('member',)


class AchievementAdmin(admin.ModelAdmin):
    autocomplete_fields = ('image',)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Membership)
admin.site.register(VerificationRequest)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(AchievementAward, AchievementAwardAdmin)
