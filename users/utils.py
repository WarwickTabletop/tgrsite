import requests
from django.http import HttpRequest
from django.template import loader

from .models import Membership, Member
from .achievements import give_achievement, give_achievement_once

from premailer import Premailer

try:
    from xml.etree.cElementTree import ElementTree, fromstring
except ImportError:
    from xml.etree.ElementTree import ElementTree, fromstring

from notifications.tasks import send_mass_html_mail
from tgrsite import settings

if settings.DEBUG:
    url = "http://"
else:
    url = "https://"
url += settings.PRIMARY_HOST

transformer = Premailer(base_url=url, base_path=url,
                        disable_leftover_css=True, disable_validation=True, remove_unset_properties=True,
                        include_star_selectors=True, keep_style_tags=False, align_floating_images=False)


def sendRequestMailings(user, token, email):
    request = HttpRequest()
    request.META['HTTP_HOST'] = settings.PRIMARY_HOST
    subject = "Membership Verification | Warwick Tabletop Games and Role-Playing Society"
    text = loader.render_to_string("users/membership/plain-email.txt", {"user": user, "host": url, "token": token},
                                   request)
    html = loader.render_to_string("users/membership/email.html", {"user": user, "token": token},
                                   request)
    html = transformer.transform(html)
    mails = [(subject, text, html, None, [email])]
    send_mass_html_mail(mails, fail_silently=False)


def getApiMembers():
    members_xml = requests.get(
        "https://www.warwicksu.com/membershipapi/listMembers/" + settings.MEMBERSHIP_API_KEY + "/")
    members_root = fromstring(members_xml.text.encode('utf-8'))
    members = {}
    for member in members_root:
        id = member.find('UniqueID').text
        email = member.find('EmailAddress').text
        members[id] = email
    return members


def updateMemberships():
    members = getApiMembers()
    for m in Membership.objects.all():
        if m.verified:
            if m.uni_id.lstrip('u') in members:
                if not m.active:
                    m.active = True
                    m.save()
                    give_achievement(m.member, "verify_membership")
            else:
                if m.active:
                    m.active = False
                    m.save()
