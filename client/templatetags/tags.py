from django import template
register = template.Library()


@register.filter
def add_class(field, css_class):
    if widget_class := field.field.widget.attrs.get("class"):
        css_class += " " + widget_class
    return field.as_widget(attrs={"class": css_class})

@register.filter
def get_price_display(offer):
    return offer.get_price_display()

@register.filter
def get_price_discounted_display(offer):
    return offer.get_price_discounted_display()