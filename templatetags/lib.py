import uuid

from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.http.response import HttpResponseRedirectBase
from django.views import View

from .models import IdempotencyToken


class HttpResponseNoContent(HttpResponse):
    """Special HTTP response with no content, just headers.

    The content operations are ignored.
    """

    def __init__(self, content="", mimetype=None, status=None, content_type=None):
        super().__init__(status=204)

        if "content-type" in self._headers:
            del self._headers["content-type"]

    def _set_content(self, value):
        pass

    def _get_content(self, value):
        pass

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

class IdempotentMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            if "_idempotency_token" in request.POST and is_valid_uuid(request.POST['_idempotency_token']):
                normalised_uuid = str(uuid.UUID(request.POST['_idempotency_token']))
                try:
                    i = IdempotencyToken.objects.get(token=normalised_uuid)
                    # Seen the request before, so need to short circuit
                    if i.redirect:
                        # Try to return saved redirect
                        return HttpResponseRedirect(i.redirect)
                    try:
                        # No redirect was saved, so try to generate one
                        return HttpResponseRedirect(self.get_success_url())
                    except Exception:
                        # Otherwise return a generic success code
                        return HttpResponseNoContent()
                except IdempotencyToken.DoesNotExist:
                    # Haven't seen this token before, so safe to do main action
                    # Save the token first to avoid repeats
                    i = IdempotencyToken.objects.create(token=normalised_uuid)
                    # Perform the intended action
                    resp = super().dispatch(request, *args, **kwargs)
                    # Save the redirect if we can
                    if isinstance(resp, HttpResponseRedirectBase):
                        i.redirect = resp.url
                        i.save()
                    return resp
            else:
                return HttpResponseBadRequest("Missing required internal form attribute")
        return super().dispatch(request, *args, **kwargs)
