from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.db import models, ProgrammingError, OperationalError

from tgrsite.utils import PermsError


class Permissions:
    _instance = None

    class AppPermissions:
        def __init__(self, app=""):
            self.app = app
            self.perms = set()
            self.final = False

        def __getattr__(self, item):
            if item in self.perms:
                return self.app + "." + item
            else:
                if PermsError():
                    raise AttributeError("Unknown Permission: " + item)

        def register(self, element):
            if not self.final:
                self.perms.add(element)
            else:
                raise RuntimeError("Attempt to register on finalised object")

        def finalise(self):
            self.final = True

    def __init__(self):
        self.apps = {}

        try:
            perms = Permission.objects.all()
            for perm in perms:
                app = perm.content_type.app_label
                if app not in self.apps:
                    self.apps[app] = Permissions.AppPermissions(app)
                self.apps[app].register(perm.codename)
            for i in self.apps.values():
                i.finalise()
        except (ProgrammingError, OperationalError):
            pass

    @classmethod
    def get(cls):
        # I hate the singleton pattern, but this time its useful.
        if cls._instance is None:
            return cls()
        return cls._instance

    def __getattr__(self, item):
        if item in self.apps:
            return self.apps[item]
        if PermsError():
            raise AttributeError("Unknown App: " + item)
        else:
            return Permissions.AppPermissions()


PERMS = Permissions.get()
