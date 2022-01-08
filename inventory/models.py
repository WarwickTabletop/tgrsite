from datetime import date

from django.db import models
from django.db.models.query import Q
from django.urls import reverse
from django.utils import timezone

from users import models as users


def daterange(start, end, step=timezone.timedelta(days=1)):
    curr = start
    while curr <= end:
        yield curr
        curr += step


# Create your models here.
class Inventory(models.Model):
    name = models.CharField(max_length=30, unique=True)
    display = models.CharField(max_length=35, blank=True)
    suggestions = models.BooleanField(default=True)
    loans = models.BooleanField(default=False)
    loan_conditions = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Inventories"

    def __str__(self):
        return self.fullname

    @property
    def fullname(self):
        return self.display if self.display else self.name

    def canonical_(self):
        return str(self.name).lower()

    def get_absolute_url(self):
        return reverse("inventory:index", kwargs={"inv": self.canonical_()})


class Record(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=1)
    image = models.URLField(blank=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    acquired = models.DateField(blank=True, null=True)
    owner = models.ForeignKey(users.Member, on_delete=models.PROTECT,
                              blank=True, null=True)  # Set if not the society's

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.inventory.name + ": " + self.name

    def get_absolute_url(self):
        return reverse("inventory:item_detail", kwargs={"inv": self.inventory.canonical_(), "pk": self.pk})

    def can_be_borrowed(self, start_date, end_date, exclude=()):
        loans = self.loan_set.filter(Q(rejected__isnull=True) &
                                     Q(start_date__lte=end_date, end_date__gte=start_date))
        print(loans)
        for day in daterange(start_date, end_date):
            count = 0
            for loan in loans:
                if loan.contains(day) and loan.is_live() and loan.id not in exclude:
                    count += 1
            if count >= self.quantity:
                return False
        return True

    def get_live_loans(self):
        return [x for x in self.loan_set.all() if x.is_live()]


class Suggestion(models.Model):
    name = models.CharField(max_length=40)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    requester = models.ForeignKey(
        users.Member, on_delete=models.SET_NULL, null=True, blank=True)  # Have to delete
    # users without deleting their request
    justification = models.TextField(
        verbose_name="Why should we buy this item?", blank=True)
    context = models.TextField(
        verbose_name="How did you discover it?", blank=True)
    link = models.URLField(blank=True, help_text="A link to where the item can be purchased. Please check Zatu for "
                                                 "availability first.")
    archived = models.BooleanField(default=False)

    def __str__(self):
        return str(self.inventory) + " " + self.name + ": " + str(self.requester)

    def get_absolute_url(self):
        return reverse("inventory:suggestion_detail", kwargs={"inv": self.inventory.canonical_(), "pk": self.pk})


class Loan(models.Model):
    class STATE:
        PENDING = 0
        REJECTED = 1
        AUTHORISED = 2
        TAKEN = 3
        COMPLETED = 4
        EXPIRED = 5

    requester = models.ForeignKey(users.Member, on_delete=models.PROTECT)
    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name="inventory_loans")
    items = models.ManyToManyField(Record)
    start_date = models.DateField()
    end_date = models.DateField()
    authorised = models.ForeignKey(users.Member, on_delete=models.PROTECT,
                                   related_name="inventory_loan_authorisations", blank=True, null=True)
    rejected = models.ForeignKey(users.Member, on_delete=models.CASCADE,
                                 related_name="inventory_loan_rejections", blank=True, null=True)
    taken_when = models.DateTimeField(blank=True, null=True)
    taken_who = models.ForeignKey(users.Member, on_delete=models.PROTECT,
                                  related_name="inventory_loan_take_witnesses", blank=True, null=True)
    returned_when = models.DateTimeField(blank=True, null=True)
    returned_who = models.ForeignKey(users.Member, on_delete=models.PROTECT,
                                     related_name="inventory_loan_return_witnesses", blank=True, null=True)
    notes = models.TextField(blank=True,
                             help_text="Notes visible only to loan administrators (damage, late, excuses ect.)")

    def on_loan(self):
        if self.taken_when is None:
            return False
        else:
            if self.returned_when is None:
                return True
            else:
                return False

    def is_live(self):
        if self.rejected or self.returned_who:
            return False
        if self.end_date < date.today():
            if self.taken_who:
                return True
            else:
                return False
        return True

    def can_edit(self):
        return not (self.authorised or self.rejected)

    def state(self):
        if self.rejected:
            return self.STATE.REJECTED
        elif self.authorised:
            if self.returned_who:
                return self.STATE.COMPLETED
            elif self.taken_who:
                return self.STATE.TAKEN
            else:
                if self.is_live():
                    return self.STATE.AUTHORISED
                else:
                    return self.STATE.EXPIRED
        else:
            if self.is_live():
                return self.STATE.PENDING
            else:
                return self.STATE.EXPIRED

    @property
    def state_text(self):
        translation = {self.STATE.AUTHORISED: "Authorised",
                       self.STATE.EXPIRED: "Expired",
                       self.STATE.TAKEN: "On Loan",
                       self.STATE.COMPLETED: "Completed",
                       self.STATE.REJECTED: "Rejected",
                       self.STATE.PENDING: "Pending"}
        return translation[self.state()]

    def __str__(self):
        # ThomasB: 20/12/18-25/12/18 (3)
        return str(self.requester) + ": " + str(self.start_date) + "-" + str(self.end_date) + "(" + str(
            self.items.all().count()) + ") - " + self.state_text

    def contains(self, check_date):
        return self.start_date <= check_date <= self.end_date

    def get_absolute_url(self):
        return reverse("inventory:loan_detail", kwargs={"inv": self.inventory.canonical_(), "pk": self.pk})

    class Meta:
        permissions = (
            ("can_authorise", "Can authorise loan"),
            ("can_witness", "Can witness withdrawal or return of items"),
            ("can_surrogate", "Can create loans on other's behalf"),
        )
