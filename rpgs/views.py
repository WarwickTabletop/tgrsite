from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.messages import add_message
from django.contrib.messages import constants as messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import F, Count, Q, Case, When, IntegerField, ExpressionWrapper
# testing
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from messaging.views import create_group
from notifications.models import NotifType
from notifications.utils import notify, notify_everybody, notify_discord
from .forms import RpgForm, RpgCreateForm
from .models import Rpg, Tag
from .templatetags.rpg_tags import can_manage, can_access
from users.models import Member
from users.achievements import give_achievement_once

def member_or_none(req):
    if not req.user.is_anonymous:
        return req.user.member
    return None

class Index(generic.ListView):
    template_name = 'rpgs/index.html'
    model = Rpg
    context_object_name = 'rpgs'
    paginate_by = 10

    def get_queryset(self):
        Rpg.objects.filter(is_in_the_past=False, finishes__lt=timezone.now()).update(is_in_the_past=True)
        member = member_or_none(self.request)
        queryset = Rpg.objects.visible(member)
        if self.request.GET.get('tag', False):
            queryset = queryset.filter(tags__name__iexact=self.request.GET['tag'])
        if self.request.GET.get('user', False):
            try:
                user = Member.objects.get(equiv_user__username__iexact=self.request.GET.get('user'))
            except Member.DoesNotExist:
                pass
            else:
                queryset = queryset.filter(Q(members=user) | Q(creator=user) | Q(game_masters=user)).distinct()
        if not self.request.GET.get('showfinished', False):
            queryset = queryset.filter(is_in_the_past=False)
        queryset = queryset.annotate(
            n_remain=ExpressionWrapper(F('players_wanted') - Count('members'), output_field=IntegerField())).annotate(
            full=Case(When(n_remain=0, then=1), default=0, output_field=IntegerField()))
        if self.request.GET.get('showfull', False) or not self.request.GET.get('isfilter', False):
            # second filter needed to detect if the filtered form has been submitted
            # as checkbox False is transmitted by omitting the attribute (stupid!)
            pass
        else:
            queryset = queryset.filter(full__exact=0)

        return queryset.order_by('published', '-pinned', 'full', '-created_at')


class Detail(UserPassesTestMixin, generic.DetailView):
    template_name = 'rpgs/detail.html'
    model = Rpg
    context_object_name = 'rpg'

    def test_func(self):
        rpg = get_object_or_404(Rpg, id=self.kwargs['pk'])
        return can_access(member_or_none(self.request), rpg)


def notify_rpg(object):
    url = reverse('rpgs:detail', kwargs={'pk': object.id})
    notify_everybody(NotifType.RPG_CREATE, f"A new event '{object.title}' is available for signup.",
                        url, merge_key=object.id)
    discord_message = (f"A new event **{object.title}** is now available for signup!\n"
                        f"**Available slots**: {object.players_wanted}")
    if object.system:
        discord_message += f"\n**System**: {object.system}"
    if object.timeslot:
        discord_message += f"\n**Timeslot**: {object.timeslot}"
    if object.location:
        discord_message += f"\n**Location**: {object.location}"
    discord_message += f"\nVisit https://www.warwicktabletop.co.uk{url} to sign up."

    notify_discord(discord_message, object.creator)
    object.published = True
    object.save()

class Create(LoginRequiredMixin, generic.CreateView):
    template_name = 'rpgs/create.html'
    model = Rpg
    form_class = RpgCreateForm

    def form_valid(self, form):
        form.instance.creator = self.request.user.member
        response = super().form_valid(form)
        for i in form.cleaned_data['tag_list']:
            tag, new = Tag.objects.get_or_create(name=i)
            self.object.tags.add(tag)
        self.object.game_masters.add(self.request.user.member)
        self.object.save()
        add_message(self.request, messages.SUCCESS, "Event successfully created")
        give_achievement_once(self.request.user.member, "first_event", request=self.request)
        if Rpg.objects.filter(creator=self.request.user.member).count() >= 5:
            give_achievement_once(self.request.user.member, "five_events", request=self.request)
        if self.object.published:
            notify_rpg(self.object)
        return response


class Update(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    template_name = 'rpgs/edit.html'
    model = Rpg
    form_class = RpgForm

    def test_func(self):
        rpg = get_object_or_404(Rpg, id=self.kwargs['pk'])
        return can_manage(self.request.user.member, rpg)

    def form_valid(self, form):
        response = super().form_valid(form)
        for i in self.object.tags.all():
            if i.name.lower() not in form.cleaned_data['tag_list']:
                self.object.tags.remove(i)

        for i in form.cleaned_data['tag_list']:
            tag, new = Tag.objects.get_or_create(name=i)
            if tag not in self.object.tags.all():
                self.object.tags.add(tag)
        self.object.save()
        add_message(self.request, messages.SUCCESS, "Event updated")
        return response


class Delete(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, generic.DeleteView):
    template_name = 'rpgs/delete.html'
    model = Rpg
    success_message = "Event Deleted"

    def get_success_url(self):
        return reverse('rpgs:index')

    def test_func(self):
        rpg = get_object_or_404(Rpg, pk=self.kwargs['pk'])
        return can_manage(self.request.user.member, rpg)


class Publish(LoginRequiredMixin, UserPassesTestMixin, generic.View):
    def __init__(self, **kwargs):
        self.rpg = None
        super().__init__(**kwargs)
    
    def test_func(self):
        self.rpg = get_object_or_404(Rpg, pk=self.kwargs['pk'])
        return can_manage(self.request.user.member, self.rpg) and not self.rpg.published

    def post(self, request, *args, **kwargs):
        notify_rpg(self.rpg)
        return HttpResponseRedirect(reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))


class Join(LoginRequiredMixin, UserPassesTestMixin, generic.View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def test_func(self):
        rpg = get_object_or_404(Rpg, id=self.kwargs['pk'])
        return can_access(member_or_none(self.request), rpg)

    def post(self, request, *args, **kwargs):
        rpg = get_object_or_404(Rpg, pk=self.kwargs['pk'])

        if self.request.user.member in rpg.members.all():
            add_message(self.request, messages.WARNING, "You are already in that event!")
        elif self.request.user.member in rpg.game_masters.all():
            add_message(self.request, messages.WARNING, "You are running that event!")
        elif rpg.members.count() >= rpg.players_wanted:
            add_message(self.request, messages.WARNING, "Sorry, the event is already full")
        elif not self.request.user.member.is_soc_member and rpg.member_only:
            add_message(self.request, messages.WARNING, "This event is only available to current members. "
                                                        "Please verify your membership from your profile and try again.")
        elif len(self.request.user.member.discord.strip()) == 0 and rpg.discord:
            add_message(self.request, messages.WARNING, "This event is being held on discord. "
                                                        "Please add a discord account to your profile and try again.")
        else:
            rpg.members.add(self.request.user.member)
            notify(rpg.creator, NotifType.RPG_JOIN,
                   'User {} joined your game "{}"!'.format(self.request.user.username, rpg.title),
                   reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))
            add_message(self.request, messages.SUCCESS, "You have successfully joined that event")
        return HttpResponseRedirect(reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))


class Leave(LoginRequiredMixin, generic.View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def post(self, *args, **kwargs):
        rpg = get_object_or_404(Rpg, pk=self.kwargs['pk'])

        if self.request.user.member not in rpg.members.all():
            add_message(self.request, messages.WARNING, "You are not currently in that event!")
        else:
            rpg.members.remove(self.request.user.member)
            notify(rpg.creator, NotifType.RPG_JOIN,
                   'User {} left your game "{}"!'.format(self.request.user.username, rpg.title),
                   reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))
            add_message(self.request, messages.SUCCESS, "You have successfully left that event")
        return HttpResponseRedirect(reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))


class Kick(LoginRequiredMixin, UserPassesTestMixin, generic.View):
    def __init__(self, **kwargs):
        self.rpg = None
        super().__init__(**kwargs)

    def test_func(self):
        self.rpg = get_object_or_404(Rpg, id=self.kwargs.get('pk'))
        return can_manage(self.request.user.member, self.rpg)

    def post(self, *args, **kwargs):
        kicked = User.objects.get(member__id=self.request.POST.get('user-to-remove')).member
        self.rpg.members.remove(kicked)
        notify(kicked, NotifType.RPG_KICK,
               'You were kicked from the game "{}".'.format(self.rpg.title),
               reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))
        add_message(self.request, messages.SUCCESS, "{} Removed from Event".format(kicked.equiv_user.username))
        return HttpResponseRedirect(reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))


class AddMember(LoginRequiredMixin, UserPassesTestMixin, generic.View):
    def __init__(self, **kwargs):
        self.rpg = None
        super().__init__(**kwargs)

    def test_func(self):
        self.rpg = get_object_or_404(Rpg, id=self.kwargs['pk'])
        return can_manage(self.request.user.member, self.rpg)

    def post(self, *args, **kwargs):
        try:
            added = User.objects.get(username__iexact=self.request.POST.get('username')).member
        except User.DoesNotExist:
            add_message(self.request, messages.WARNING, "Username not found")
        else:
            if self.rpg.members.count() >= self.rpg.players_wanted:
                add_message(self.request, messages.WARNING, "Game is full")
            else:
                self.rpg.members.add(added)
                notify(added, NotifType.RPG_KICK,
                       'You were added to the game "{}".'.format(self.rpg.title),
                       reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))
                add_message(self.request, messages.SUCCESS, "{} Added to Event".format(added.equiv_user.username))
        return HttpResponseRedirect(reverse('rpgs:detail', kwargs={'pk': self.kwargs['pk']}))


class MessageGroup(LoginRequiredMixin, UserPassesTestMixin, generic.RedirectView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rpg = None

    def test_func(self):
        self.rpg = get_object_or_404(Rpg, id=self.kwargs['pk'])
        return self.request.user.member in self.rpg.members.all() or self.request.user.member in self.rpg.game_masters.all()

    def get_redirect_url(self, *args, **kwargs):
        members = {*self.rpg.members.all(), *self.rpg.game_masters.all()}
        if self.rpg.messaging_thread:
            self.rpg.messaging_thread.participants.set(members)
            return reverse("message:message_thread", kwargs={'pk': self.rpg.messaging_thread.pk})
        else:
            group = create_group(*members, name=self.rpg.title)
            self.rpg.messaging_thread = group
            self.rpg.save()
            add_message(self.request, messages.WARNING,
                        "Please note, if the people in the event change you will need to "
                        "click again to update the messaging group.")
            return reverse("message:message_thread", kwargs={'pk': group.pk})


def alltags(request):
    tags = [x.name for x in Tag.objects.all().order_by('name')]
    return JsonResponse(tags, safe=False)
