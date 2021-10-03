from django import template

register = template.Library()


@register.simple_tag
def can_manage(member, rpg):
    if not member:
        return False
    # whether given user has permission to manage given rpg
    # Not used as a tag - when this logic is changed be sure to update detail.html!
    return (member == rpg.creator) or (member in list(rpg.game_masters.all())) or (
        member.equiv_user.has_perm('rpgs.change_rpg'))


@register.simple_tag
def can_access(member, rpg):
    if rpg.published:
        return True
    if not member:
        return False
    return (member == rpg.creator) or (member in list(rpg.game_masters.all()) or
                                       (member in rpg.members.all()) or member.equiv_user.has_perm('rpgs.view_rpg'))


@register.filter
def has_accessible_children(rpg, member):
    return any(can_access(member, r) for r in rpg.children.all())


@register.filter
def has_signed_up_to_child(member, rpg):
    return any((member in r.members.all()) for r in rpg.children.all())


# todo: assignment tag is deprecated
@register.simple_tag(takes_context=True)
def is_player(context, rpg):
    return rpg.members.filter(id=context.request.user.member.id)
