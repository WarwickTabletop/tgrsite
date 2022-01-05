from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate

from messaging.models import Message

from getpass import getpass

class Command(BaseCommand):
    help = 'Censor your messages containing sensitive information.'

    def handle(self, *args, **kwargs):
        self.stdout.write("""This service is for censoring messages containing sensitive information.
You can send passwords to the exec that need them, and then censor the messages
containing those passwords directly using this tool.

First, you need to log in to access your messages.""")
        username = input("Enter website username: ")
        password = getpass("Enter website password: ")
        user = authenticate(username=username, password=password)
        if user is None:
            self.stdout.write("Could not authenticate!")
            return
        self.stdout.write("""Authenticated. Please enter the sensitive information that you wish to censor.
Every message containing that substring will be censored. As such, you may
enter a substring of that sensitive information, as long as it uniquely
identifies it.""")
        sensitive = ""
        confirm = " "
        while sensitive != confirm:
            sensitive = getpass("Enter sensitive information: ")
            confirm = getpass("Please enter that information again: ")
        for m in Message.objects.filter(sender=user.member):
            if m.content.find(sensitive) != -1:
                title = m.thread.title
                if title is None or title == '':
                    members = list(m.thread.participants.all())
                    member_usernames = map(lambda member: member.equiv_user.username, members)
                    title = ",".join(member_usernames)
                self.stdout.write(f"Message to {m.thread.participants} censored:\n{self.style.SUCCESS(m.content.replace(sensitive, '*' * len(sensitive)))}")
                m.content = "(This message has been censored.)"
                m.save()
        self.stdout.write("Censored all relevant messages.")