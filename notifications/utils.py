from datetime import timedelta
import requests

from django.utils import timezone

from notifications.models import NotificationSubscriptions, SubType, Notification
from users.models import Member
from website_settings.models import StringProperty


def notify(member, notif_type, content, url, merge_key=None):
    sub, new = NotificationSubscriptions.objects.get_or_create(member=member)
    if sub.get_category_subscription(notif_type) != SubType.NONE:
        n = create_notification(member, notif_type, content, url, merge_key)
        # Not strictly needed as all data is generated, but good practice...
        n.full_clean()
        n.save()
        delete_old(member)


def create_notification(member, notif_type, content, url, merge_key=None):
    return Notification(member=member, notif_type=notif_type, content=content, url=url, is_unread=True,
                        is_emailed=False, merge_key=merge_key,
                        time=timezone.now())


def create_notification_if_subbed(member, notif_type, content, url, merge_key=None):
    sub, new = NotificationSubscriptions.objects.get_or_create(member=member)
    if sub.get_category_subscription(notif_type) != SubType.NONE:
        return create_notification(member, notif_type, content, url, merge_key)
    else:
        return None


def delete_old(member):
    week_ago = timezone.now() - timedelta(days=7)
    year_ago = timezone.now() - timedelta(days=365)
    Notification.objects.filter(
        member=member, is_unread=False, time__lt=week_ago).delete()
    Notification.objects.filter(member=member, time__lt=year_ago).delete()


def delete_all_old():
    # Delete anything over 1 week old that has been read, and everything more than a year old
    week_ago = timezone.now() - timedelta(days=7)
    year_ago = timezone.now() - timedelta(days=365)
    Notification.objects.filter(is_unread=False, time__lt=week_ago).delete()
    Notification.objects.filter(time__lt=year_ago).delete()


def notify_bulk(members, notif_type, content, url, merge_key=None):
    notifs = [create_notification_if_subbed(
        m, notif_type, content, url, merge_key) for m in members]
    notifications = list(filter(None, notifs))
    Notification.objects.bulk_create(notifications)
    delete_all_old()


def notify_everybody(notif_type, content, url, merge_key=None):
    notify_bulk(Member.objects.all(), notif_type, content, url, merge_key)


def notify_discord(content, member=None):
    discord_url, new = StringProperty.objects.get_or_create(
        key="notifications_webhook_url")
    if discord_url.value != "":
        data = {'content': content}
        if member is not None:
            assert isinstance(member, Member)
            data['username'] = member.username
            data['avatar_url'] = member.gravatar()
        requests.post(discord_url.value, data=data)
