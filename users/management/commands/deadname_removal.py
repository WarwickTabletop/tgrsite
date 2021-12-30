from django.core.management.base import BaseCommand

from newsletters.models import Newsletter
from pages.models import Page
from minutes.models import Meeting

from enum import Enum
from titlecase import titlecase
import re

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
        return titlecase(target)

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
    results = []
    for apos in [False, True]:
        n = apostrophe(needle) if apos else needle
        results.append(tag_results(all_results(n, haystack), MatchLabel(CapitalisationType.LOWERCASE, apos)))
        results.append(tag_results(all_results(n.upper(), haystack), MatchLabel(CapitalisationType.UPPERCASE, apos)))
        results.append(tag_results(all_results(titlecase(n), haystack), MatchLabel(CapitalisationType.TITLECASE, apos)))
    combined = [j for i in results for j in i]
    combined.sort(key=lambda pair: pair[0])
    return combined

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
    def give_context(self, index, needle, haystack, size=100):
        return self.style.SUCCESS(haystack[max(index-size, 0):index])\
            + self.style.NOTICE(needle) + self.style.SUCCESS(haystack[index+len(needle):index+len(needle)+size])
    
    def perform_substitutions(self, id_string, needle, new_needle, haystack):
        substitutions = search_for(needle, haystack)
        if substitutions == []:
            return haystack, False
        
        self.stdout.write(f"Matches found in {id_string}!")
        self.subs_sources.append(id_string)

        mod = 0
        sub_made = False
        for (index, label) in substitutions:
            # When we perform a substitution, the indices calculated at the start of the perform_substitutions call
            # may become out of date (if the replacement string has a different length). This mod tracks the change
            # in length and modifies all indices to work with the updated string.
            index_mod = index + mod
            needle_caps = to_capitalisation(label, needle)
            new_needle_caps = to_capitalisation(label, new_needle)
            self.stdout.write(self.give_context(index_mod, needle_caps, haystack))
            self.stdout.write(f"Type 'yes' to substitute {needle_caps} for {new_needle_caps}.")
            self.stdout.write("Type 'no' to not perform this substitution.")
            inp = ""
            while inp != "yes" and inp != "no":
                inp = input("Choice: ")
            if inp == "yes":
                haystack = haystack[0:index_mod] + new_needle_caps + haystack[index_mod+len(needle):len(haystack)]
                sub_made = True
                mod += len(new_needle_caps) - len(needle_caps)
                self.stdout.write("Substitution made.")
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
1. This does a simple find-and-replace over various parts of the website -
   newsletters, hosted pages (including Exec History) and meeting minutes.
   This does _not_ edit parts of the website that aren't "official society
   communication". Those edits will be up to individuals to make.
   Since this is just a find-and-replace, it only replaces names and not
   pronouns. You will have to deal with pronouns yourself for the most part.
2. You should only perform a find-and-replace if you are sure that the name
   in question is the correct one.
   It turns out multiple people can have the same name! Some context will be
   provided to help discern this, as well as a link to the full original
   source.
3. This does not attempt any optical character recognition, so cannot read
   images. You'll have to check images of things like tournament standings
   yourself.
   Alt text containing the deadname will be flagged up as such, as you'll
   likely have to change the image also.
   You can check for additional alt text keywords to identify images where
   the person may have been deadnames (e.g. 'mtg', 'netrunner', 'tournament').
   This does not guarantee all offending images will be found however, so you
   should still manually check afterwards.
4. Only perform this process if the person has actively asked for it.
   There are a variety of reasons that someone might not want this process to
   have been done, such as not being out to employers who want evidence of work
   done at the society.
5. This does not perform any changes on Discord or Facebook. You'll have to do 
   those yourself.

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
            n.body, sub3 = self.perform_substitutions(identify_newsletter("Body", n),
                dead, real, n.body)
            if sub1 or sub2 or sub3:
                n.save()
        self.stdout.write("""Would you like to look for specific alt-text in
newsletter images?
This can help identify images that might contain deadnames.
Example alt-text you might look for is 'mtg' or 'magic' for a Magic player to
try and find tournament standings.

Enter your search terms separated by commas if you'd like to look for them, or
leave it blank if you want to skip this step. For example, for the above Magic
player you might enter:
mtg,magic,tournament
""")
        term_str = input("Search terms:")
        terms = term_str.split(",")
        for term in terms:
            if term != "":
                for n in Newsletter.objects.all():
                    if re.search(f"\[.+?{term}.+?\]\(.+?\)", n.body):
                        id_string = identify_newsletter("Body", n)
                        self.stdout.write(f"Found term {term} in alt-text in: {id_string}!")
                        self.subs_sources.append(f"(found term {term}) {id_string}")

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