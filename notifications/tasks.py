from django.conf import settings
from django.core import mail
from django.http.request import HttpRequest
from django.template import loader

from newsletters.models import Newsletter
from notifications.models import Notification, SubType, NotificationSubscriptions
from users.models import Member

from premailer import Premailer

if settings.DEBUG:
    url = "http://"
else:
    url = "https://"
url += settings.PRIMARY_HOST

transformer = Premailer(base_url=url, base_path=url,
                        disable_leftover_css=True, disable_validation=True, remove_unset_properties=True,
                        include_star_selectors=True, keep_style_tags=False, align_floating_images=False)


def doSummaryNotificationMailings():
    users = Member.objects.all()
    user_notifications = {u.id: [] for u in users}

    notifications = Notification.objects.filter(
        is_emailed=False, is_unread=True).order_by('-time')
    for notification in notifications:
        sub, new = NotificationSubscriptions.objects.get_or_create(
            member=notification.member)
        if sub.get_category_subscription(notification.notif_type) == SubType.SUMMARY:
            user_notifications[notification.member_id].append(notification)

    mails = []
    request = HttpRequest()
    request.META['HTTP_HOST'] = settings.PRIMARY_HOST

    def generateEmail(noti, user):
        text = loader.render_to_string("notifications/plain-summary-email.txt",
                                       {"notifications": noti,
                                        "user": user}, request)
        html = loader.render_to_string("notifications/summary-email.html",
                                       {"notifications": noti,
                                        "user": user}, request)
        html = transformer.transform(html)
        return text, html

    for pk in user_notifications.keys():
        noti = user_notifications[pk]
        user = Member.objects.get(pk=pk).equiv_user
        if len(noti) > 0:
            text, html = generateEmail(noti, user)
            mails.append(('Warwick Tabletop Activity Summary',
                          text, html,
                          None, [user.email]))

    send_mass_html_mail(mails, fail_silently=False)
    Notification.objects.filter(is_emailed=False).update(is_emailed=True)


def doNewsletterMailings(pk):
    request = HttpRequest()
    request.META['HTTP_HOST'] = settings.PRIMARY_HOST
    subs = NotificationSubscriptions.objects.filter(
        newsletter__exact=SubType.FULL)
    newsletter = Newsletter.objects.get(pk=pk)
    subject = newsletter.title + " | Warwick Tabletop Games and Roleplaying Society"
    text = loader.render_to_string("newsletters/plain-email-version.txt", {"object": newsletter},
                                   request)
    html = loader.render_to_string("newsletters/email-version.html", {"object": newsletter, "unsub": True},
                                   request)
    html = transformer.transform(html)
    mails = [(subject, text, html, None, [sub.member.equiv_user.email])
             for sub in subs]
    send_mass_html_mail(mails, fail_silently=False)


def send_mass_html_mail(datatuple, fail_silently=False, auth_user=None,
                        auth_password=None, connection=None):
    """
    Given a datatuple of (subject, message, html_message, from_email,
    recipient_list), send each message to each recipient list.
    Return the number of emails sent.
    If from_email is None, use the DEFAULT_FROM_EMAIL setting.
    If auth_user and auth_password are set, use them to log in.
    If auth_user is None, use the EMAIL_HOST_USER setting.
    If auth_password is None, use the EMAIL_HOST_PASSWORD setting.
    """
    connection = connection or mail.get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )
    messages = [
        mail.EmailMultiAlternatives(subject, message, sender, recipient,
                                    alternatives=[(html_message, 'text/html')],
                                    connection=connection)
        for subject, message, html_message, sender, recipient in datatuple
    ]
    return connection.send_messages(messages)
