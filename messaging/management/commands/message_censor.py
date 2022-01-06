from django.core.management.base import BaseCommand
from users.models import User

from messaging.models import Message

from getpass import getpass

class Command(BaseCommand):
    help = 'Censor your messages containing sensitive information.'

    def handle(self, *args, **kwargs):
        self.stdout.write("""This service is for censoring messages containing sensitive information.
You can send passwords to the exec that need them, and then censor the messages
containing those passwords directly using this tool.
"""
            + self.style.ERROR("ONLY USE THIS TOOL ON MESSAGES FOR WHICH YOU HAVE PERMISSION TO DO SO.\n\n")
            + "First, provide the username for which you'd like to censor their messages.")
        username = input("Enter website username: ")
        user = User.objects.filter(username=username).first()
        if user is None:
            self.stdout.write("Could not find that user!")
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
                self.stdout.write(f"Message {m.thread} censored:\n{self.style.SUCCESS(m.content.replace(sensitive, '*' * len(sensitive)))}")
                m.content = "(This message has been censored.)"
                m.save()
        self.stdout.write("Censored all relevant messages.")