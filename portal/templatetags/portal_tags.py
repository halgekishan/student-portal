from django import template

register = template.Library()

@register.filter
def dict_key(d, key):
    return d.get(key, [])

@register.filter
def get_item(lst, index):
    try:
        return lst[index]
    except (IndexError, KeyError):
        return ''
