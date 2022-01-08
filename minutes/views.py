from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, reverse
from django.contrib.auth.mixins import PermissionRequiredMixin as PRMBase
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.views.generic import DetailView, CreateView, UpdateView

from .models import Folder, Meeting
from .forms import MeetingForm


class PermissionRequiredMixin(PRMBase):
    def handle_no_permission(self):
        messages.add_message(self.request, messages.ERROR,
                             "You don't have permission to perform that action.")
        if self.raise_exception or self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse("minutes:index"))
        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())


# Create your views here.
class MeetingDetail(DetailView):
    model = Meeting
    template_name = "minutes/detail.html"

    def get_queryset(self):
        super().get_queryset()
        folders = Folder.roots()
        folder = None
        for i in self.kwargs['folder'].split("/"):
            try:
                folder = folders.get(name__iexact=i)
                folders = folder.children.all()
            except (Folder.MultipleObjectsReturned, Folder.DoesNotExist):
                raise Http404("Unknown folder")
        if folder is None:
            raise Http404("Unknown folder")
        return folder.meetings.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        try:
            item = queryset.get(name__iexact=self.kwargs['name'])
        except ObjectDoesNotExist:
            raise Http404("No meeting found with that address")
        except MultipleObjectsReturned:
            raise Http404("Ambiguous record: please refine")

        return item

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        meetings = list(Meeting.objects.order_by('date'))
        index_of = meetings.index(self.object)
        ctxt['next'] = meetings[index_of + 1] if index_of + \
            1 < len(meetings) else None
        ctxt['prev'] = meetings[index_of - 1] if index_of - 1 >= 0 else None
        return ctxt


class CreateMeeting(PermissionRequiredMixin, CreateView):
    permission_required = "minutes.add_meeting"
    model = Meeting
    form_class = MeetingForm
    template_name = "minutes/edit.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        form.instance.author = self.request.user.member
        return super().form_valid(form)


class UpdateMeeting(PermissionRequiredMixin, UpdateView):
    permission_required = "minutes.change_meeting"
    model = Meeting
    form_class = MeetingForm
    template_name = "minutes/edit.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        return super().form_valid(form)


def meetingBounce(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    return HttpResponseRedirect(meeting.get_absolute_url())


def index(request):
    meeting = Meeting.objects.latest("date")
    return HttpResponseRedirect(meeting.get_absolute_url())
