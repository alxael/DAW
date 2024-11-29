from django import template
register = template.Library()


@register.filter
def add_class(field, css_class):
    if widget_class := field.field.widget.attrs.get("class"):
        css_class += " " + widget_class
    return field.as_widget(attrs={"class": css_class})


@register.inclusion_tag('components/footer.html')
def show_footer():
    return
