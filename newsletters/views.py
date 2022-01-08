from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.generic import UpdateView, CreateView, DeleteView
from premailer import Premailer

from notifications.models import NotifType
from notifications.utils import notify_everybody
from notifications.tasks import doNewsletterMailings
from django.conf import settings
from website_settings.models import TextProperty
from .forms import NewsletterForm
from .models import Newsletter

if settings.DEBUG:
    url = "http://"
else:
    url = "https://"
url += settings.PRIMARY_HOST
transformer = Premailer(base_url=url, base_path=url,
                        disable_leftover_css=True, disable_validation=True, remove_unset_properties=True,
                        include_star_selectors=True, keep_style_tags=False, align_floating_images=False)


class Index(generic.ListView):
    model = Newsletter
    ordering = ('ispublished', '-pub_date')
    paginate_by = 20


class Detail(generic.DetailView):
    model = Newsletter

    def get_object(self, queryset=None):
        obj = super(Detail, self).get_object()
        if not obj.ispublished and not self.request.user.has_perm('newsletters.view_newsletter'):
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        newsletters = list(Newsletter.objects.filter(ispublished=True).order_by('pub_date'))
        if self.object.ispublished:
            index_of = newsletters.index(self.object)
            ctxt['next'] = newsletters[index_of + 1] if index_of + 1 < len(newsletters) else None
            ctxt['prev'] = newsletters[index_of - 1] if index_of - 1 >= 0 else None
        return ctxt


class Preview(Detail):
    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        new_response = HttpResponse(transformer.transform(response.rendered_content), charset=response.charset)
        return new_response


class Create(PermissionRequiredMixin, CreateView):
    model = Newsletter
    form_class = NewsletterForm

    permission_required = 'newsletters.add_newsletter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wide"] = True
        return context

    def get_initial(self):
        initial = super().get_initial()
        template, d = TextProperty.objects.get_or_create(key='newsletter_template', defaults="")
        initial['body'] = str(template.value)
        return initial

    def form_valid(self, form):
        form.instance.author = self.request.user.member
        form.instance.pub_date = timezone.now()
        s = super(Create, self).form_valid(form)
        if form.instance.ispublished:
            notify_everybody(NotifType.NEWSLETTER,
                             'The newsletter "{}" has been published!'.format(form.instance.title),
                             form.instance.get_absolute_url())
        return s

    def get_success_url(self):
        if self.object.ispublished:
            doNewsletterMailings(self.object.id)
        return super().get_success_url()


class Update(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Newsletter
    form_class = NewsletterForm

    permission_required = 'newsletters.change_newsletter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wide"] = True
        return context

    def form_valid(self, form):
        should_mail = False
        # If newsletter goes from unpublished to published.
        if form.instance.ispublished and not Newsletter.objects.get(id=form.instance.id).ispublished:
            form.instance.pub_date = timezone.now()
            notify_everybody(NotifType.NEWSLETTER,
                             'The newsletter "{}" has been published!'.format(form.instance.title),
                             form.instance.get_absolute_url())
            should_mail = True
        response = super(Update, self).form_valid(form)
        if should_mail:
            doNewsletterMailings(form.instance.id)  # Need to defer this after super to send with latest changes
        return response

    def form_invalid(self, form):
        super().render_to_response(form)

    def test_func(self):
        obj = get_object_or_404(Newsletter, pk=self.kwargs['pk'])
        if obj.author and (
                obj.author != self.request.user.member and not self.request.user.has_perm('newsletters.modify_others')):
            # If neither owned it nor have modify_others
            return False
        else:
            return True


def latest(req):
    letter = Newsletter.objects.order_by('-pub_date').filter(ispublished=True)[0]
    return redirect(letter)


class Delete(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Newsletter
    permission_required = 'newsletters.delete_newsletter'
    success_url = reverse_lazy('newsletters:newsletters_index')

    def test_func(self):
        obj = get_object_or_404(Newsletter, pk=self.kwargs['pk'])
        if obj.author and (obj.author != self.request.user.member and not self.request.user.has_perm(
                'newsletters.modify_others')):
            return False
        else:
            return True
