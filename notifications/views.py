from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.messages import add_message
from django.contrib.messages import constants as messages
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import render, get_object_or_404, reverse
from django.urls import reverse_lazy
from django.views.generic import UpdateView, ListView, RedirectView, View

from .forms import SubscriptionForm
from .models import Notification, NotificationSubscriptions, SubType
from .utils import delete_old


class UpdateSubscriptions(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = NotificationSubscriptions
    form_class = SubscriptionForm
    template_name = "notifications/preferences.html"
    success_url = reverse_lazy("homepage")

    def get_queryset(self):
        data, new = NotificationSubscriptions.objects.get_or_create(
            member=self.request.user.member)
        return data

    def get_object(self, queryset=None):
        data, new = NotificationSubscriptions.objects.get_or_create(
            member=self.request.user.member)
        return data

    def get_success_message(self, cleaned_data):
        return "Personal Subscription Settings Updated!"


class QuickNewsletterSubscribe(LoginRequiredMixin, View):
    def post(self, request):
        member = request.user.member
        notification_subs, new = NotificationSubscriptions.objects.get_or_create(
            member=member)
        notification_subs.newsletter = SubType.FULL
        notification_subs.full_clean()
        notification_subs.save()
        add_message(request, messages.SUCCESS,
                    "You have subscribed to the newsletter.")
        return HttpResponseRedirect(reverse("users:me"))

    def get(self, request):
        return render(request, 'notifications/newsletter_subscribe.html')


# Debug only. Probably should remove from prod...
@login_required
def email_notifications(request):
    context = {
        'notifications': Notification.objects.filter(member=request.user.member, is_unread=True).order_by('-time'),
    }
    return render(request, 'notifications/summary-email.html', context)


class AllNotifications(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/index.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        return Notification.objects.filter(member=self.request.user.member).order_by('-is_unread', '-time')


class ReadAll(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(
            member=request.user.member).update(is_unread=False)
        delete_old(request.user.member)
        return HttpResponseRedirect(reverse('notifications:all_notifications'))


class ReadNotification(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    def __init__(self):
        self.object = None
        super().__init__()

    def test_func(self):
        self.object = Notification.objects.get(id=self.kwargs['pk'])
        return self.object.member == self.request.user.member

    def get_redirect_url(self, *args, **kwargs):
        self.object.is_unread = False
        self.object.save()
        delete_old(self.request.user.member)
        if self.object.url:
            return self.object.url
        else:
            return reverse('notifications:all_notifications')
