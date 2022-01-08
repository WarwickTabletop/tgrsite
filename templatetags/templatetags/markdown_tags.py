from django import template
from django.templatetags import static
from django.utils.safestring import mark_safe
from markdown import markdown
from bleach.sanitizer import Cleaner

register = template.Library()
exts = ['markdown.extensions.nl2br',
        'pymdownx.caret', 'pymdownx.tilde', 'sane_lists']
safe_exts = ['pymdownx.caret', 'pymdownx.tilde', 'sane_lists', 'attr_list']


@register.filter(is_safe=True)
def parse_md(value):
    return md_bleach(markdown(break_tags(value), extensions=exts, output_format='html5'))


@register.filter(is_safe=True)
def parse_md_text(value):
    return md_bleach_imgless(markdown(break_tags(value), extensions=exts, output_format='html5'))


# Parses markdown WITHOUT escaping. Use with caution!
@register.filter(is_safe=True)
def parse_md_safe(value):
    return mark_safe(markdown(value, extensions=safe_exts, output_format='html5'))


class FullStaticNode(static.StaticNode):
    def url(self, context):
        request = context['request']
        return request.build_absolute_uri(super().url(context))


@register.tag('fullstatic')
def do_static(parser, token):
    return FullStaticNode.handle_token(parser, token)


def break_tags(text):
    # Provides no security, but makes casual tag insertion fail
    return text.replace('<', '&lt;')


def md_bleach(text):
    cleaner = Cleaner(tags=['p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'em', 'strong', 'a', 'ul', 'ol', 'li',
                            'blockquote', 'img', 'pre', 'code', 'hr', 'del'],
                      attributes={'a': ['href'], 'img': ['src', 'alt']}, protocols=['http', 'https'])
    text = cleaner.clean(text)
    return mark_safe(text)


def md_bleach_imgless(text):
    cleaner = Cleaner(tags=['p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'em', 'strong', 'a', 'ul', 'ol', 'li',
                            'blockquote', 'pre', 'code', 'hr', 'del'],
                      attributes={'a': ['href']}, protocols=['http', 'https'], strip=True)
    text = cleaner.clean(text)
    return mark_safe(text)
