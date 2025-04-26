from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter(name='rupee')
def rupee(value):
    """Format a value as Indian Rupees (₹)"""
    if value is None:
        return "₹0.00"
    
    formatted_value = floatformat(value, 2)
    return f"₹{formatted_value}"
