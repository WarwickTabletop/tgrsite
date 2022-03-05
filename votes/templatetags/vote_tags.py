import hashlib
import math
import random

from django import template

from votes.models import Election

register = template.Library()


@register.filter()
def sanitized_vote_count(vote: Election):
    value = vote.votes().count()
    if value <= 5:
        return "0-5"
    else:
        seed = hashlib.sha1((str(vote.id) + str(vote.name) + str(value)).encode('utf-8'))
        generator = random.Random()
        generator.seed(seed)
        fuzzed = generator.randrange(math.floor(value * 0.8), math.ceil(value * 1.2))
        return f"{math.floor(fuzzed * 0.8)}-{math.ceil(fuzzed * 1.2)}"


@register.simple_tag(takes_context=True)
def current_user_ticket(context, election: Election):
    try:
        return election.ticket_set.filter(member=context['user'].member).first()
    except AttributeError:
        return None