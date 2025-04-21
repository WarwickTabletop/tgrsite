from django.db import models
from django.shortcuts import reverse

from users.models import Member

body_size = 32768


class Forum(models.Model):
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='subforums')

    sort_index = models.IntegerField(default=0,
                                     help_text='Index for sorting. Lower value = earlier in list.')

    title = models.CharField(max_length=64, verbose_name="Name")
    description = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.title

    def get_parents(self):
        if self.parent is None:
            return []
        tree = []
        seen = {}
        # walk up through tree to root
        x = self.parent
        while True:
            tree.append(x)
            seen[x.pk] = True
            if x.parent is not None and x.parent.pk not in seen:
                # traverse upwards
                x = x.parent
            else:
                # reached root or loop parent
                break
        return reversed(tree)

    # string that represents the forum's location
    # eg "Roleplaying / LARP / Character Sheets"
    # might be useful to generalise this for Threads
    def get_parent_tree(self):
        tree = [str(x) for x in self.get_parents()]
        if not tree:
            return '-'
        return ' / '.join(tree)

    get_parent_tree.short_description = 'Location'

    # QuerySet of subforums
    def get_subforums(self):
        return Forum.objects.filter(parent=self.id)

    # list of string representations of subforums
    def get_subforums_str(self):
        return [str(x) for x in self.get_subforums()]

    get_subforums.short_description = 'Subforums'
    get_subforums_str.short_description = 'Subforums'

    @staticmethod
    def get_parentless_forums():
        return Forum.objects.filter(parent__isnull=True)

    def get_threads_count(self):
        return Thread.objects.filter(forum=self.id).count()

    get_threads_count.short_description = 'threads'

    # recursively get thread count
    # i.e. number of threads here and in all subforums
    def get_threads_count_r(self, seen=None):
        if seen is None:
            seen = {self.pk: True}
        count = 0
        for subforum in self.get_subforums():
            if not subforum.pk in seen:
                seen[subforum.pk] = True
                count += subforum.get_threads_count_r(seen)
        return count + self.get_threads_count()

    def get_latest_post(self):
        return self.thread_set.latest('pub_date')

    def get_absolute_url(self):
        return reverse("forum:subforum", args=(self.pk,))


# return self.thread_set.order_by('pub_date').reverse()[:1][::-1]

class Thread(models.Model):
    # cascade because we need to be able to delete forums maybe?
    # in which case forumless threads will either die,
    # or need to be moved -before- the forum is deleted
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)

    title = models.CharField(max_length=128)
    body = models.TextField(max_length=body_size)
    pub_date = models.DateTimeField('date posted')

    # pinned/stickied/whatever threads will show up before all others in their forums
    is_pinned = models.BooleanField(default=False)

    # prevents people not admin from replying to a thread
    is_locked = models.BooleanField(default=False)

    # until we implement proper banning/deactivation, just cascade
    author = models.ForeignKey(Member, on_delete=models.CASCADE)

    # people subscribed to updates
    subscribed = models.ManyToManyField(
        Member, related_name="thread_notification_subscriptions")

    def __str__(self):
        return self.title

    def get_author(self):
        return Member.objects.get(id=self.author.id).equiv_user.username

    get_author.short_description = 'Author'

    def get_response_count(self):
        return Response.objects.filter(thread=self.id).count()

    def last_update(self):
        try:
            return self.response_set.latest('pub_date').pub_date
        except Response.DoesNotExist as e:
            return self.pub_date

    def get_all_authors(self):
        authors = [x.author for x in self.response_set.all()]
        authors.append(self.author)
        return list(set(authors))

    def get_absolute_url(self):
        return reverse("forum:viewthread", args=(self.id,))


# a reply in a forum thread
# there are fundamental similarities between thread OPs and responses;
# but the decision was made early to put the latter as part of the Thread class...
class Response(models.Model):
    # when a thread is deleted its responses are deleted
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    body = models.TextField(max_length=body_size)

    pub_date = models.DateTimeField('date posted', auto_now_add=True)
    author = models.ForeignKey(Member, on_delete=models.CASCADE)

    def __str__(self):
        # TODO: probably strip markdown
        return f"{self.thread}: {self.author}"

    def get_author(self):
        return Member.objects.get(id=self.author.id)

    get_author.short_description = 'Author'

    def get_absolute_url(self):
        return reverse("forum:viewthread", args=(self.thread_id,)) + "#response-" + str(self.pk)
