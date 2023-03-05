import math

from django import template
from django.utils.safestring import mark_safe

from votes.models import Election

register = template.Library()


@register.filter()
def sanitized_vote_count(vote: Election):
    value = vote.votes().count()
    if value <= 5:
        return mark_safe("&le; 5")
    else:
        return f"{math.floor(value/5)*5} - {math.ceil(value/5)*5}"


@register.simple_tag(takes_context=True)
def current_user_ticket(context, election: Election):
    try:
        return election.ticket_set.filter(member=context['user'].member).first()
    except AttributeError:
        return None


@register.simple_tag()
def vote_breakdown_table(election: Election):
    actions = election.stvresult.action_log
    print(actions)
    if actions is None:
        return {}
    candidates = [str(x.id) for x in election.candidate_set.all()]  # JSON keys have to be strings
    if len(candidates) <= election.seats:
        return {}  # No logs created if election didn't have enough candidates
    scores = {candidate:[] for candidate in candidates}
    states = {candidate:["HOPEFUL"] for candidate in candidates} # States are offset by one round due to r0
    wastage = []
    total = []
    threshold = []
    tiebreak = [False]
    shortcircuit = False
    for i in actions:
        type_ = i["type"]
        detail = i["details"]
        if type_ == "round" and not shortcircuit:
            tiebreak.append(False)
            sum_ = detail['wastage']
            wastage.append(detail['wastage'])
            threshold.append(detail['threshold'])
            for candidate in candidates:
                scores[candidate].append(
                    detail['candidates'][candidate]['votes']
                )
                states[candidate].append(detail['candidates'][candidate]['status'])
                sum_ += detail['candidates'][candidate]['votes']
            total.append(sum_)
            elected = sum([1 for x in detail['candidates'].values() if x['status']=='ELECTED'])
            if elected == election.seats:
                shortcircuit = True
                sum_ = detail['wastage']
                for candidate in candidates:
                    status = detail['candidates'][candidate]['status']
                    if status == 'HOPEFUL':
                        status = 'DEFEATED'
                    states[candidate].append(status)
                    scores[candidate].append(detail['candidates'][candidate]['votes'])
                    sum_ += detail['candidates'][candidate]['votes']
                total.append(sum_)
                wastage.append(detail['wastage'])
                threshold.append(detail['threshold'])

    if not shortcircuit:
        for candidate in candidates:
            scores[candidate].append(scores[candidate][-1])
            status = states[candidate][-1]
            if status == 'HOPEFUL':
                status = 'ELECTED'
            states[candidate].append(status)
        wastage.append(wastage[-1])
        total.append(total[-1])
        threshold.append(threshold[-1])

    for i in actions:
        type_ = i["type"]
        detail = i["details"]
        if type_ == "tiebreak":
            if int(detail['round']) < len(wastage):
                tiebreak[int(detail['round'])-1] = (detail['choice'],detail['candidates'])

    table_header=[]
    # Each cell is (content, rowspan, "header"|"changed"|"standard")
    rounds = len(wastage)
    print(tiebreak, wastage, total, threshold, scores,states)
    header1 = [(election.name,1,'header')]
    for i in range(rounds):
        if tiebreak[i] is not False:
            header1.append((f"Round {i}",3,'header'))
        else:
            header1.append((f"Round {i}", 2, 'header'))
    header1.append((f"", 1, 'header'))
    table_header.append(header1)

    header2 = [("Candidate",1,'header')]
    for i in range(rounds):
        header2.append((f"State",1,'header'))
        header2.append((f"Votes", 1, 'header'))
        if tiebreak[i] is not False:
            header2.append((f"Tie", 1, 'header'))
    header2.append((f"State",1,'header'))
    table_header.append(header2)
    table = []
    for candidate in election.candidate_set.all():
        row = []
        key = str(candidate.id)
        row.append((candidate.name,1,'standard'))
        row.append((states[key][0],1,"standard"))
        for i in range(rounds):
            row.append((scores[key][0], 1, "float"))
            if tiebreak[i] is not False:
                if key == tiebreak[i][0]:
                    row.append((mark_safe('<i class="fas fa-check-circle"></i>'), 1, "standard"))
                elif key in tiebreak[i][1]:
                    row.append((mark_safe('<i class="fas fa-circle"></i>'), 1, "standard"))
                else:
                    row.append(("", 1, "standard"))
            if states[key][i] == states[key][i+1]:
                row.append((states[key][i+1], 1, "standard"))
            else:
                row.append((states[key][i + 1], 1, "changed"))

        table.append(row)

    footer1 = [("Wastage",1,'header'),("",1,'standard'),]
    for i in range(rounds):
        footer1.append((wastage[i],1,'float'))
        footer1.append(("",1,'standard'))
        if tiebreak[i] is not False:
            footer1.append(("", 1, 'standard'))
    table.append(footer1)

    footer2 = [("Total Votes", 1, 'header'), ("", 1, 'standard'), ]
    for i in range(rounds):
        footer2.append((total[i], 1, 'float'))
        footer2.append(("", 1, 'standard'))
        if tiebreak[i] is not False:
            footer2.append(("", 1, 'standard'))
    table.append(footer2)

    footer3 = [("Threshold", 1, 'standard'), ("", 1, 'standard'), ]
    for i in range(rounds):
        footer3.append((threshold[i], 1, 'float'))
        footer3.append(("", 1, 'standard'))
        if tiebreak[i] is not False:
            footer3.append(("", 1, 'standard'))
    table.append(footer3)

    return {'head':table_header, 'body':table}
