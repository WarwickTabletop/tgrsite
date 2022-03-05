import uuid as uuid
from django.db import models

from users.models import Member


# Create your models here.
class Election(models.Model):
    class Types(models.IntegerChoices):
        FPTP = 0, "First past the post"
        APRV = 1, "Approval vote"
        STV = 2, "Single Transferable Vote"

    name = models.CharField(max_length=50)
    description = models.TextField()
    vote_type = models.IntegerField(choices=Types.choices, default=Types.FPTP)
    max_votes = models.IntegerField(default=2,
                                    help_text="Ignored except in Plurality. Number of candidates selectable per vote")
    seats = models.IntegerField(
        default=1, help_text="Ignored except in STV. Number of people who can win")
    open = models.BooleanField(default=False)
    archive = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def votes(self):
        if self.vote_type == Election.Types.FPTP:
            return self.fptpvote_set.all()
        elif self.vote_type == Election.Types.APRV:
            return self.aprvvote_set.all()
        elif self.vote_type == Election.Types.STV:
            return self.stvvote_set.all()
        else:
            raise NotImplemented()


class Candidate(models.Model):
    class State(models.IntegerChoices):
        STANDING = 0, "Standing"
        WITHDRAWN = 1, "Withdrawn"

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    state = models.IntegerField(choices=State.choices, default=State.STANDING)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def formid(self):
        return "option_" + str(self.election.id) + "_" + str(self.id)

    def votes(self):
        return self.election.votes().filter(selection=self.id)


class Ticket(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    uuid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    spent = models.BooleanField(default=False)

    def __str__(self):
        return str(self.uuid)

    class Meta:
        unique_together = (('member', 'election'),)


class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    uuid = models.UUIDField(unique=True)
    time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.uuid)


class FPTPVote(Vote):
    selection = models.ForeignKey(Candidate, models.CASCADE)


class APRVVote(Vote):
    selection = models.ManyToManyField(Candidate)


class STVVote(Vote):
    selection = models.ManyToManyField(Candidate, through='STVPreference')


class STVPreference(models.Model):
    order = models.IntegerField()
    stvvote = models.ForeignKey(STVVote, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    class Meta:
        ordering = ['order']


class STVResult(models.Model):
    election = models.OneToOneField(Election, on_delete=models.CASCADE)
    full_log = models.TextField()
    winners = models.ManyToManyField(Candidate)
    generated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.election)
