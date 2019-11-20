from django import template

register = template.Library()


@register.filter(name='color')
def color(index):
    color_list = ["red", "orange", "yellow", "olive", "green", "teal", "blue", "violet", "purple", "pink", "brown",
                  "grey", "black"]
    return color_list[index]
