from django.contrib.auth.models import User
from django.test import TestCase

from users.views import spawn_user
from .models import Rpg


def get_member(*usernames):
    members = []
    for x in usernames:
        members.append(User.objects.get(username=x).member)
    return tuple(members)


class Rpgs(TestCase):
    users = {}
    rpg = None

    def setUp(self):
        alice = spawn_user('alice', 'alice@tagarople.com', 'zstOBwZ9Oe').member
        spawn_user('bob', 'bob@tagarople.com', 'fkL7HbcP8i')
        spawn_user('eve', 'eve@tagarople.com', 'XZVrUFm3oy')
        ash = spawn_user('ash', 'ash@sent.com', 'CSXgzrned3').member

        rpg = Rpg(title='test case RPG', players_wanted=2,
                  timeslot="Thursday", creator_id=ash.id)
        rpg.save()
        rpg.game_masters.add(ash)
        rpg.members.add(alice)

    def test_contains_player(self):
        alice, bob, eve, ash = get_member('alice', 'bob', 'eve', 'ash')
        rpg = Rpg.objects.get()
        self.assertTrue(alice in rpg.members.all())
        self.assertFalse(bob in rpg.members.all())
        self.assertFalse(eve in rpg.members.all())
        self.assertFalse(ash in rpg.members.all())
