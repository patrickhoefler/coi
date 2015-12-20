import datetime
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def sparkline_url(values):
    "Create a nice Google Charts sparkline"
    if values:
        def divide(a,b): return round(float(a) / b * 95, 1)
        maxValue = []
        if max(values) > 0:
            maxValue.append(max(values))
        else:
            maxValue.append(1)
        normalizedValues = map(divide, values, len(values) * maxValue)
        joinedValues = ",".join(map(str,normalizedValues))
        return mark_safe('http://chart.apis.google.com/chart?cht=lc&chs=100x20&chd=t:' + joinedValues + \
                         '&chco=3F65A6&chls=1,1,0&chxt=r,x,y&chxs=0,990000,11,0,_|1,990000,1,0,_|2,990000,1,0,_&chxl=0:||1:||2:||')
    else:
        return ''


@register.filter
def img_left(img_url, style='default'):
    "Turn an image URL into an img tag and make it float to the left"
    if img_url:

        css = 'float: left; padding-right: 10px;'
        if style == 'default':
            css += 'width: 64px;'
        elif style == 'feed':
            css += 'width: 100px; padding-bottom: 5px;'

        return mark_safe('<img src="' + img_url + '" style="' + css + '" />')

    else:
        return ''

@register.filter
def img_right(img_url, style='default'):
    "Turn an image URL into an img tag and make it float to the right"
    if img_url:

        css = 'float: right; padding-left: 10px;'
        if style == 'default':
            css += 'width: 64px;'

        return mark_safe('<img src="' + img_url + '" style="' + css + '" />')

    else:
        return ''

@register.filter
def age_chart_values(published, days=2):
    time_passed_percent = int((datetime.datetime.utcnow() - published).total_seconds() / datetime.timedelta(days=days).total_seconds() * 100)
    time_left_percent = 100 - time_passed_percent
    return ','.join([str(time_passed_percent), str(time_left_percent)])
