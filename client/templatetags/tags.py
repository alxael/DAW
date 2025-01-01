import logging
from django import template
from django.conf import settings

register = template.Library()
logger = logging.getLogger("django")


@register.filter
def add_class(field, css_class):
    if widget_class := field.field.widget.attrs.get("class"):
        css_class += " " + widget_class
    return field.as_widget(attrs={"class": css_class})


@register.filter
def get_price_display(offer, currency_conversion):
    logger.info(offer.get_price(currency_conversion))
    return offer.get_price(currency_conversion)


@register.filter
def get_price_discounted_display(offer, currency_conversion):
    return offer.get_price_discounted(currency_conversion)


@register.simple_tag
def default_currency():
    return settings.DEFAULT_CURRENCY_CODE
