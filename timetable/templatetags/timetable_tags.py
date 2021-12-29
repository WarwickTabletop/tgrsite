from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from timetable.models import RoomLink

register = template.Library()


@register.filter
def for_event(weeks, event):
    result = []
    oldBookingTxt = True
    bookingTxt = None
    run = 1
    for week in weeks:
        try:
            bookingTxt = week.booking_set.filter(event=event)[0].room
        except IndexError:
            bookingTxt = None

        if bookingTxt == oldBookingTxt:
            run += 1
        else:
            result.append((run, oldBookingTxt))
            run = 1
            oldBookingTxt = bookingTxt
    if bookingTxt == oldBookingTxt:
        result.append((run, oldBookingTxt))
    return result[1:]


affixes = '*^+-!&%$#@=?'
affix_map = {ord(i): None for i in affixes}


@register.simple_tag
def room_link(r, _class):
    # Remove all special characters from affixes.
    rooms = r.split(",")
    rooms = [i.strip().translate(affix_map) for i in rooms]
    results = []
    for room in rooms:
        roomlink = None
        # print(room)
        if len(room) > 0:
            try:
                roomlink = RoomLink.objects.get(room__iexact=room)
            except (RoomLink.DoesNotExist, RoomLink.MultipleObjectsReturned):
                roomlink = RoomLink.objects.filter(room__icontains=room).first()
        if roomlink is None:
            results.append(room)
        else:
            results.append(format_html('<a target="_blank" rel="noopener noreferrer" href="{}" class="{}">{}</a>',
                roomlink.url, _class, room))
    return mark_safe(", ".join(results))
