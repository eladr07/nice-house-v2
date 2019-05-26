from django import template

register = template.Library()

@register.filter
def commaise(value):
    try:
        value = int(value)
    except:
        return value
    if value < 0:
        return '-' + commaise(value*-1)
    elif value < 1000:
        return str(value)
    else:
        return commaise(value/1000) + ',' + str(value % 1000).rjust(3, '0')
    
@register.filter
def attrsum(value, arg):
    return sum([getattr(item, arg) or 0 for item in value])