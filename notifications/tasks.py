import django

django.setup()
from django.conf import settings
from django.core import mail
from django.template import loader
from django.http.request import HttpRequest

from users.models import Member
from notifications.models import Notification, SubType, NotificationSubscriptions
from newsletters.models import Newsletter


def doSummaryNotificationMailings():
    users = Member.objects.all()
    user_notifications = {u.id: [] for u in users}

    notifications = Notification.objects.filter(is_emailed=False, is_unread=True).order_by('-time')
    for notification in notifications:
        sub, new = NotificationSubscriptions.objects.get_or_create(member=notification.member)
        if sub.get_category_subscription(notification.notif_type) == SubType.SUMMARY:
            user_notifications[notification.member_id].append(notification)

    mails = []
    request = HttpRequest()
    request.META['HTTP_HOST'] = settings.ALLOWED_HOSTS[0]
    for pk in user_notifications.keys():
        noti = user_notifications[pk]
        user = Member.objects.get(pk=pk).equiv_user
        if len(noti) > 0:
            mails.append(('Warwick Tabletop Activity Summary',
                          loader.render_to_string("notifications/plain-summary-email.txt", {"notifications": noti,
                                                                                            "user": user},
                                                  request),
                          loader.render_to_string("notifications/summary-email.html", {"notifications": noti,
                                                                                       "user": user},
                                                  request),
                          None, [user.email]))

    send_mass_html_mail(mails, fail_silently=True, )
    Notification.objects.filter(is_emailed=False).update(is_emailed=True)


def doNewsletterMailings(pk):
    request = HttpRequest()
    request.META['HTTP_HOST'] = settings.ALLOWED_HOSTS[0]
    subs = NotificationSubscriptions.objects.filter(newsletter__exact=SubType.FULL)
    newsletter = Newsletter.objects.get(pk=pk)
    subject = newsletter.title + " | Warwick Tabletop and Role-Playing Society"
    text = loader.render_to_string("newsletters/plain-email-version.txt", {"object": newsletter},
                                   request)
    html = loader.render_to_string("newsletters/email-version.html", {"object": newsletter, "unsub": True},
                                   request)

    mails = [(subject, text, html, None, [sub.member.equiv_user.email]) for sub in subs]
    send_mass_html_mail(mails, fail_silently=True)


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


if __name__ == '__main__':
    doSummaryNotificationMailings()