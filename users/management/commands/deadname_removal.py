from django.core.management.base import BaseCommand

from newsletters.models import Newsletter
from pages.models import Page
from minutes.models import Meeting

from enum import Enum

class CapitalisationType(Enum):
    LOWERCASE = 1
    UPPERCASE = 2
    TITLECASE = 3

class MatchLabel():
    capitalisation : CapitalisationType = CapitalisationType.LOWERCASE
    apostrophe = False

    def __init__(self, cap, apos):
        self.capitalisation = cap
        self.apostrophe = apos

def to_capitalisation(label, target):
    captype = label.capitalisation
    if label.apostrophe: target = apostrophe(target)
    if captype == CapitalisationType.LOWERCASE:
        return target.lower()
    if captype == CapitalisationType.UPPERCASE:
        return target.upper()
    if captype == CapitalisationType.TITLECASE:
        return target.title()

def all_results(needle, haystack):
    index = 0
    result = []
    while index < len(haystack):
        res = haystack.find(needle, index)
        if res != -1:
            result.append(res)
            index = res + 1
        else:
            break
    return result

def tag_results(results, tag):
    return list(map(lambda x: (x, tag), results))

# Returns all indices of needle in haystack, along with capitalisation type.
def search_for(needle, haystack):
    for apos in [False, True]:
        n = apostrophe(needle) if apos else needle
        lowercase = tag_results(all_results(n, haystack), MatchLabel(CapitalisationType.LOWERCASE, apos))
        uppercase = tag_results(all_results(n.upper(), haystack), MatchLabel(CapitalisationType.UPPERCASE, apos))
        titlecase = tag_results(all_results(n.title(), haystack), MatchLabel(CapitalisationType.TITLECASE, apos))
    return (lowercase + uppercase + titlecase).sort(key=lambda pair: pair[0])

def give_context(index, haystack, size=100):
    # TODO: make this context highlight the target.
    return haystack[max(index-size, 0):index+size]

def identify_newsletter(noun, newsletter):
    return f"{noun} of newsletter #{newsletter.id} (https://www.warwicktabletop.co.uk/newsletters/{newsletter.id})"
def identify_page(noun, page):
    return f"{noun} of page #{page.id} (https://www.warwicktabletop.co.uk/page/{page.name})"
def identify_minutes(noun, minutes):
    return f"{noun} of minutes #{minutes.id} (https://www.warwicktabletop.co.uk/minutes/{minutes.folder.canonical_()}/{minutes.name})"

def apostrophe(s):
    if s[-1] == 's':
        return s + "'"
    return s + "'s"

class Command(BaseCommand):
    help = "`deadname_removal deadname realname` searches all text entries for a deadname and helps you replace it."
    subs_sources = []

    def must_be(self, s, x):
        inp = input(s)
        if inp == x:
            return
        else:
            self.must_be(s, x)
    
    def perform_substitutions(self, id_string, needle, new_needle, haystack):
        substitutions = search_for(needle, haystack)
        if substitutions == []:
            return haystack, False
        
        self.stdout.write(f"Matches found in {id_string}!")
        self.subs_sources.append(id_string)

        mod = 0
        sub_made = False
        for (index, label) in substitutions:
            self.stdout.write(give_context(index, haystack))
            needle_caps = to_capitalisation(label, needle)
            new_needle_caps = to_capitalisation(label, new_needle)
            self.stdout.write(f"Type 'yes' to substitute {needle_caps} for {new_needle_caps}.")
            self.stdout.write("Type 'no' to not perform this substitution.")
            inp = ""
            while inp != "yes" and inp != "no":
                inp = input("Choice: ")
            if inp == "yes":
                index_mod = index + mod
                haystack = haystack[0:index_mod] + new_needle_caps + haystack[index_mod+len(needle):len(haystack)]
                sub_made = True
                mod += len(new_needle_caps) - len(needle_caps)
                self.stdout.write("Substitution not made.")
            if inp == "no":
                self.stdout.write("Substitution not made.")

            self.stdout.write("")
        
        return haystack, sub_made
    
    def add_arguments(self, parser):
        parser.add_argument("deadname", type=str)
        parser.add_argument("realname", type=str)

    def handle(self, *args, **options):
        self.stdout.write("""This program is for finding and replacing deadnames present on the website.
This comes with a few disclaimers, which you **must** heed:
1. This does a simple find-and-replace over various parts of the website - newsletters, hosted pages (including Exec History) and meeting minutes.
   This does _not_ edit parts of the website that aren't "official society communication". Those edits will be up to individuals to make.
   Since this is just a find-and-replace, it only replaces names and not pronouns. You will have to deal with pronouns yourself for the most part.
2. You should only perform a find-and-replace if you are sure that the name in question is the correct one.
   It turns out multiple people can have the same name! Some context will be provided to help discern this, as well as a link to the full original source.
3. This does not attempt any optical character recognition, so cannot read images. You'll have to check images of things like tournament standings yourself.
   Alt text containing the deadname will be flagged up as such, as you'll likely have to change the image also.
   You can check for additional alt text keywords to identify images where the person may have been deadnames (e.g. 'magic', 'netrunner', 'tournament').
   This does not guarantee all offending images will be found however, so you should still manually check afterwards.
4. Only perform this process if the person has actively asked for it.
   There are a variety of reasons that someone might not want this process to have been done, such as not being out to employers who want evidence of work done at the society.
5. This does not perform any changes on Discord or Facebook. You'll have to do those yourself.

Please type out 'yes' to confirm that you understand this.""")
        self.must_be("Confirm: ", "yes")
        self.stdout.write("Thank you!")
        self.stdout.write("We'll start with the newsletters. Searching through all newsletters!")
        dead, real = options['deadname'].lower(), options['realname'].lower()
        for n in Newsletter.objects.all():
            n.title, sub1 = self.perform_substitutions(identify_newsletter("Title", n),
                dead, real, n.title)
            n.summary, sub2 = self.perform_substitutions(identify_newsletter("Summary", n),
                dead, real, n.summary)
            # TODO: body needs to be searched for alt text keywords.
            n.body, sub3 = self.perform_substitutions(identify_newsletter("Body", n),
                dead, real, n.body)
            if sub1 or sub2 or sub3:
                n.save()
        self.stdout.write("Done with newsletters!")
        self.stdout.write("Cool, now doing pages. Please be careful when applying substitutions directly to HTML!")
        for p in Page.objects.all():
            p.title, sub1 = self.perform_substitutions(identify_page("Title", p),
                dead, real, p.title)
            p.page_title, sub2 = self.perform_substitutions(identify_page("Page Title", p),
                dead, real, p.page_title)
            p.body, sub3 = self.perform_substitutions(identify_page("Body", p),
                dead, real, p.body)
            if sub1 or sub2 or sub3:
                p.save()
        self.stdout.write("Done with pages!")
        self.stdout.write("Cool, finally doing meeting minutes. Searching through all minutes!")
        for m in Meeting.objects.all():
            m.title, sub1 = self.perform_substitutions(identify_minutes("Title", m),
                dead, real, m.title)
            m.body, sub2 = self.perform_substitutions(identify_minutes("Body", m),
                dead, real, m.body)
            if sub1 or sub2:
                m.save()
        self.stdout.write("Deadname removal completed. Report of changes made:")
        for sub in self.subs_sources:
            self.stdout.write(sub)