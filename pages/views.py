from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages import add_message, WARNING

from .models import Page
from users.achievements import give_this_achievement_once


class ViewPage(UserPassesTestMixin, generic.DetailView):
    model = Page
    slug_field = 'name'
    slug_url_kwarg = 'name'
    context_object_name = 'page'
    template_name = "pages/page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.get_object().breadcrumb_child == "":
            context["no_breadcrumbs"] = True
        return context

    def test_func(self):
        if not self.test_page_perms():
            return False
        o = self.get_object()
        if o.achievement and self.request.user.is_authenticated:
            give_this_achievement_once(self.request.user.member, o.achievement, request=self.request)
        return True

    def test_page_perms(self):
        if self.request.user.is_superuser:
            return True
        o = self.get_object()
        if o.permission == Page.Permissions.PUBLIC:
            return True
        if self.request.user.is_authenticated:
            if o.permission == Page.Permissions.USER:
                return self.request.user.is_authenticated
            elif o.permission == Page.Permissions.MEMBER:
                return (self.request.user.member.is_exec()
                        or self.request.user.member.is_ex_exec()
                        or self.request.user.member.is_soc_member)
            elif o.permission == Page.Permissions.EX_EXEC:
                return (self.request.user.member.is_exec()
                        or self.request.user.member.is_ex_exec())
            elif o.permission == Page.Permissions.EXEC:
                return self.request.user.member.is_exec()
            else:
                raise NotImplemented("Invalid Page Permission Value")
        else:
            add_message(self.request, WARNING, "Please log in to see that page")
            return False
