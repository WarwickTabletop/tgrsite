from django.db.models import Count, Max, F, Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages import add_message as django_add_message
from django.contrib import messages as django_message
from django.http import HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, ListView, View, RedirectView, TemplateView
from django.shortcuts import get_object_or_404, reverse
from django.utils.timezone import datetime

from notifications.models import NotifType
from notifications.utils import notify, notify_bulk
from users.models import Member
from users.permissions import PERMS
from users.achievements import give_achievement_once
from .models import Message, MessageThread, MessageReport
from .forms import QuickDM, Respond, MemberFormset


# not a view
# helper function to send messages
from .utils import visible


def create_group(*members, name=""):
    members = set(members)
    m_thread = MessageThread.objects.create(title=name)
    for member in members:
        m_thread.participants.add(member)
    m_thread.save()
    return m_thread


def find_dm(*members):
    members = set(members)
    query = MessageThread.objects.all()
    query = query.filter(dmthread=True).annotate(num_participants=Count('participants')).filter(
        num_participants=len(members))
    for i in members:
        query = query.filter(participants=i)
    print(query)
    if query.exists():
        return query.first()
    else:
        m_thread = MessageThread.objects.create(dmthread=True)
        for member in members:
            m_thread.participants.add(member)
        m_thread.save()
        return m_thread


def send_message(member, thread, message, request=None):
    # Send the notification to everyone in the thread except the sender.
    url = reverse('message:message_thread', args=[thread.id])
    for receiver in thread.participants.all():
        message_txt = 'You got a message from ' + \
            str(member.equiv_user.username)
        if thread.title:
            message_txt += ' in chat "' + str(thread.title) + '"'
        message_txt += ': ' + visible(message)
        if member != receiver:
            notify(receiver, NotifType.MESSAGE,
                   message_txt, url)
    give_achievement_once(member, "messaged", request=request)
    return Message.objects.create(sender=member, thread=thread, content=message)


@login_required
@require_http_methods(["POST"])
def rename_thread(request):
    target = get_object_or_404(MessageThread, pk=request.POST.get('thread'))

    if request.user.member not in target.participants.all():
        raise Http404()

    target.title = request.POST.get('rename', None)
    target.full_clean()
    target.save()
    return HttpResponseRedirect(reverse('message:message_thread', kwargs={'pk': request.POST.get('thread')}))


class DeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_object(self):
        if 'message' not in self.request.POST:
            raise ValueError('Missing required post field')
        m_id = self.request.POST.get('message')
        message = get_object_or_404(Message, id=m_id)
        return message

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest("Missing required post fields")

    def test_func(self):
        message = self.get_object()
        if self.request.user.member == message.sender or self.request.user.has_perm(PERMS.messaging.can_moderate):
            return True
        else:
            return False

    def post(self, request):
        message = self.get_object()
        message.deleted = datetime.now()
        message.save()
        django_add_message(request, django_message.SUCCESS,
                           "Message successfully deleted")
        if self.request.user.member == message.sender:
            return HttpResponseRedirect(reverse('message:message_thread', kwargs={'pk': message.thread_id}))
        else:
            # moderator must have done it
            return HttpResponseRedirect(reverse('message:message_thread_full', kwargs={'thread': message.thread_id}))


class ReportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_object(self):
        if 'message' not in self.request.POST:
            raise ValueError('Missing required post field')
        m_id = self.request.POST.get('message')
        message = get_object_or_404(Message, id=m_id)
        return message

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest("Missing required post fields")

    def test_func(self):
        message = self.get_object()
        if (self.request.user.member in message.thread.participants.all()
                or self.request.user.has_perm(PERMS.messaging.can_moderate)):
            return True
        else:
            return False

    def post(self, request):
        message = self.get_object()
        comment = self.request.POST.get('comment', default="")
        MessageReport.objects.create(
            member=self.request.user.member, message=message, comment=comment)
        django_add_message(request, django_message.SUCCESS,
                           "A report has been sent. An admin should review this message soon")
        notify_bulk(Member.users_with_perm(PERMS.messaging.can_moderate),
                    NotifType.OTHER,
                    f"A message has been reported for moderation by {request.user.member.username}",
                    reverse('message:message_thread_full', args=[message.thread_id]))
        return HttpResponseRedirect(reverse('message:message_thread', kwargs={'pk': message.thread_id}))


class ResolveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_object(self):
        if 'report' not in self.request.POST:
            raise ValueError('Missing required post field')
        m_id = self.request.POST.get('report')
        report = get_object_or_404(MessageReport, id=m_id)
        return report

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest("Missing required post fields")

    def test_func(self):
        return self.request.user.has_perm(PERMS.messaging.can_moderate)

    def post(self, request):
        comment = self.request.POST.get('comment', default="")
        report = self.get_object()
        report.resolved = True
        report.resolution = comment
        report.clean()
        report.save()
        django_add_message(request, django_message.SUCCESS,
                           "Report resolved successfully.")
        return HttpResponseRedirect(reverse('message:pending_reports'))


class Index(LoginRequiredMixin, FormView):
    form_class = QuickDM
    template_name = "messaging/index.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        threads = MessageThread.objects.filter(participants=self.request.user.member).annotate(
            latest=Max('message__timestamp', filter=Q(message__deleted__isnull=True)))
        ctxt['threads'] = threads.order_by(F('latest').desc(nulls_last=True))

        return ctxt

    def get_success_url(self):
        return reverse("message:message_thread", args=[self.object.thread_id])

    def form_valid(self, form):
        target = form.cleaned_data['recipient']
        assert isinstance(target, Member)
        print(target.__repr__())
        t = find_dm(target, self.request.user.member)
        if t is None:
            raise ValueError
        m = send_message(self.request.user.member, t,
                         form.cleaned_data['message'], self.request)
        self.object = m
        return super().form_valid(form)


class Reports(PermissionRequiredMixin, TemplateView):
    template_name = "messaging/reports.html"
    permission_required = PERMS.messaging.can_moderate

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        threads = MessageThread.objects.filter(message__messagereport__resolved=False).annotate(
            latest=Max('message__timestamp'))
        ctxt['threads'] = threads.order_by(F('latest').desc(nulls_last=True))
        return ctxt


class Thread(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = Respond
    template_name = "messaging/detail.html"

    def test_func(self):
        thread = get_object_or_404(MessageThread, id=self.kwargs['pk'])
        # make sure the user is in the thread
        return self.request.user.member in thread.participants.all()

    def get_context_data(self, **kwargs):
        count = 10
        ctxt = super().get_context_data(**kwargs)
        ctxt['thread'] = thread = get_object_or_404(
            MessageThread, id=self.kwargs['pk'])
        messages = thread.message_set.filter(deleted__isnull=True)
        ctxt['thread_messages'] = messages.order_by('-timestamp')[:count]
        ctxt['more'] = (messages.count() > count)
        return ctxt

    def get_success_url(self):
        return reverse("message:message_thread", args=[self.object.thread_id])

    def form_valid(self, form):
        t = MessageThread.objects.get(pk=self.kwargs['pk'])
        m = send_message(self.request.user.member, t,
                         form.cleaned_data['message'], self.request)
        self.object = m
        return super().form_valid(form)


class CreateGroup(LoginRequiredMixin, FormView):
    template_name = "messaging/newgroup.html"
    form_class = MemberFormset

    def get_success_url(self):
        return reverse("message:message_thread", args=[self.object.pk])

    def form_valid(self, form):
        members = set()
        for subform in form:
            # print(subform.cleaned_data)
            if subform.is_bound and 'recipient' in subform.cleaned_data:
                r = subform.cleaned_data['recipient']
                if r not in members:
                    members.add(r)
        if self.request.user.member not in members:
            members.add(self.request.user.member)

        self.object = create_group(*members)
        return super().form_valid(form)


class FullThread(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Message
    paginate_by = 30
    template_name = "messaging/fullthread.html"
    context_object_name = "thread_messages"

    def test_func(self):
        self.thread = thread = get_object_or_404(
            MessageThread, id=self.kwargs['thread'])
        # make sure the user is in the thread
        return self.request.user.member in thread.participants.all() or (
            self.request.user.has_perm(PERMS.messaging.can_moderate) and thread.message_set.filter(
                messagereport__resolved=False).exists())

    def get_context_data(self, object_list=None, **kwargs):
        ctxt = super().get_context_data(object_list=object_list, **kwargs)
        ctxt['thread'] = get_object_or_404(
            MessageThread, id=self.kwargs['thread'])
        if self.request.user.member not in ctxt['thread'].participants.all():
            ctxt['moderating'] = True
        return ctxt

    def get_queryset(self):
        thread_ = get_object_or_404(MessageThread, pk=self.kwargs['thread'])
        if self.request.user.has_perm(PERMS.messaging.can_moderate) and self.thread.reported():
            return thread_.message_set.order_by('-timestamp').all()
        else:
            return thread_.message_set.order_by('-timestamp').filter(deleted__isnull=True)


class DMThread(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        rec = Member.objects.get(id=kwargs['recipient'])
        q = find_dm(self.request.user.member, rec)
        return reverse("message:message_thread", args=[q.id])
