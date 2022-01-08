from django.core.management.base import BaseCommand

from forum.models import Thread


class Command(BaseCommand):
    help = 'Migrates forum subscriptions to match old rules'

    def handle(self, *args, **options):
        count = Thread.objects.count()
        i = 0
        for thread in Thread.objects.all():
            i += 1
            if i % 20 == 0:
                self.stdout.write(
                    'Progress: {:4.1f}%'.format((i * 100) / count))
            authors = thread.get_all_authors()
            for member in authors:
                if member not in thread.subscribed.all():
                    thread.subscribed.add(member)
        self.stdout.write('Forum Subscriptions Migrated')
