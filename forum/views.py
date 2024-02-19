from django.contrib.messages import add_message, constants
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, AccessMixin
from django.http import HttpResponseRedirect

from notifications.models import NotifType
from notifications.utils import notify
from .forms import ThreadForm, ResponseForm
from .models import Thread, Response, Forum
from users.achievements import give_achievement_once


class RootForum(ListView):
    model = Forum
    template_name = "forum/forum.html"
    context_object_name = "forums"

    def get_queryset(self):
        return Forum.get_parentless_forums().order_by('sort_index')


class Recent(TemplateView):
    template_name = "forum/recent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        threads = Thread.objects.order_by('-pub_date')[:5]
        responses = Response.objects.order_by('-pub_date')[:5]
        context.update({
            'threads': threads,
            'responses': responses,
        })
        return context


class ViewSubforum(AccessMixin, SuccessMessageMixin, CreateView):
    model = Thread
    form_class = ThreadForm
    template_name = "forum/subforum.html"
    success_message = "Thread successfully created"

    def post(self, request, *args, **kwargs):
        # Login required but only for post
        if not request.user.is_authenticated:
            self.handle_no_permission()
        else:
            give_achievement_once(request.user.member,
                                  "created_thread", request=request)
            return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_forum = get_object_or_404(Forum, id=self.kwargs['forum'])
        # put pinned/stickied threads first
        threads = Thread.objects.filter(forum_id=self.kwargs['forum']).extra(
            order_by=['-is_pinned'])
        context.update({
            'current': current_forum,
            'forums': current_forum.get_subforums().order_by('sort_index'),
            'threads': sorted(threads, key=lambda s:(s.is_pinned, s.last_update()), reverse=True)
        })
        return context

    def form_valid(self, form):
        """
        title=form.cleaned_data['title'],
        body=form.cleaned_data['body'],
        author=request.user.member,
        pub_date=timezone.now(),
        forum=Forum.objects.get(id=request.POST.get('forum')),
        """
        form.instance.author = self.request.user.member
        form.instance.pub_date = timezone.now()
        form.instance.forum = Forum.objects.get(id=self.kwargs['forum'])
        response = super().form_valid(form)
        Thread.objects.get(id=form.instance.id).subscribed.add(
            self.request.user.member)
        return response


class ViewThread(AccessMixin, SuccessMessageMixin, CreateView):
    model = Response
    form_class = ResponseForm
    template_name = "forum/thread.html"
    success_message = "Response successfully created"

    def post(self, request, *args, **kwargs):
        # Login required but only for post
        if not request.user.is_authenticated:
            self.handle_no_permission()
        else:
            thread = get_object_or_404(Thread, id=self.kwargs['thread'])
            if thread.is_locked and not request.user.has_perm('forum.add_response'):
                add_message(request, constants.ERROR,
                            "Sorry, this thread is locked. No responses can be created")
                self.handle_no_permission()
            else:
                give_achievement_once(
                    request.user.member, "replied_forum", request=request)
                return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'thread': get_object_or_404(Thread, id=self.kwargs['thread']),
            'responses': Response.objects.filter(thread=self.kwargs['thread']).order_by('pub_date'),
        })
        return context

    def form_valid(self, form):
        """
        body=form.cleaned_data['body'],
        author=request.user.member,
        pub_date=timezone.now(),
        thread=thread,
        """
        thread = Thread.objects.get(id=self.kwargs['thread'])

        form.instance.author = self.request.user.member
        form.instance.pub_date = timezone.now()
        form.instance.thread = thread
        response = super().form_valid(form)
        # Create Notifications
        url = reverse('forum:viewthread', kwargs={'thread': self.kwargs['thread']}) + "#response-" + str(
            form.instance.id)
        for author in thread.subscribed.all():
            if author != self.request.user.member:
                notify(author, NotifType.FORUM_REPLY,
                       '{} replied to a thread you\'ve subscribed to!'.format(
                           self.request.user.username), url,
                       thread.id)
        if self.request.user.member not in thread.subscribed.all():
            thread.subscribed.add(self.request.user.member)
        return response


class ChangeSubscription(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        sub = True if 'subscribe' in request.POST else False
        unsub = True if 'unsubscribe' in request.POST else False
        user = request.user.member
        thread = Thread.objects.get(pk=request.POST['thread'])
        if unsub:
            if user in thread.subscribed.all():
                thread.subscribed.remove(user)
        elif sub:
            if user not in thread.subscribed.all():
                thread.subscribed.add(user)
        return HttpResponseRedirect(thread.get_absolute_url())


class DeleteThread(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Thread
    success_message = "Thread Deleted"
    template_name = "forum/delete_thread.html"

    def test_func(self):
        thread = get_object_or_404(Thread, id=self.kwargs['pk'])
        return self.request.user.member == thread.author or self.request.user.has_perm('forum.delete_thread')

    def get_success_url(self):
        return reverse('forum:subforum', kwargs={'forum': self.object.forum.id})


class DeleteResponse(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Response
    success_message = "Response Deleted"
    template_name = "forum/delete_response.html"

    def test_func(self):
        response = get_object_or_404(Response, id=self.kwargs['pk'])
        return self.request.user.member == response.author or self.request.user.has_perm('forum.delete_response')

    def get_success_url(self):
        return reverse('forum:viewthread', kwargs={'thread': self.object.thread.id})


class EditResponse(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Response
    form_class = ResponseForm
    template_name = "forum/edit_response.html"
    success_message = "Response changed"

    def test_func(self):
        response = get_object_or_404(Response, id=self.kwargs['pk'])
        return self.request.user.member == response.author or self.request.user.has_perm('forum.change_response')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class EditThread(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Thread
    # I'm uncomfortable with letting people move threads around willy-nilly. Will review
    form_class = ThreadForm
    template_name = "forum/edit_thread.html"
    success_message = "Thread changed"

    def test_func(self):
        thread = get_object_or_404(Thread, id=self.kwargs['pk'])
        return self.request.user.member == thread.author or self.request.user.has_perm('forum.change_thread')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
