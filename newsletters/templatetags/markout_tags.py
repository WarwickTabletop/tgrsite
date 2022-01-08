import re

from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

register = template.Library()
exts = ['markdown.extensions.nl2br', 'pymdownx.caret', 'pymdownx.tilde']


@register.filter(is_safe=True)
def tidy_md(value):
    text = value
    text = re.sub(r"<style>[\s\S]*?<\/style>", "", text)  # Remove style blocks
    text = strip_tags(text)
    lines = text.splitlines()
    text = ""
    for i in lines:
        if len(i) > 0:
            if i[0] == "#":  # Uppercase headings
                i = i.upper()
                i = i.replace("#", "")
                if len(i) > 0 and i[0] == " ":
                    i = i[1:]
        text = text + i + '\r\n'
    text = text.replace("**", "")
    text = text.replace("`", "|")
    # Yay! REGEX!!! I recommend regexr.com to work out what this means:
    text = re.sub(r"{[^{}\n\r]*}", "", text)  # Remove { blarg } attr blocks
    text = re.sub(r"!\[([^\]\[]*)\]\(([^()]*)\)",
                  r"Image: \1", text)  # Strip image links
    # Convert square bracket links to colon
    text = re.sub(r"\[([^\]\[]*)\]\(", r"\1: (", text)
    text = re.sub(r"\\(.)", r"\1", text)  # Remove escaping from chars
    while "\r\n\r\n\r\n" in text:
        text = text.replace("\r\n\r\n\r\n", "\r\n")

    if len(text) > 2 and text[0:1] == "\r\n":
        text = text[2:]
    return mark_safe(text)
