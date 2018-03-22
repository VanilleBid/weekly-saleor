import json

import bleach
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import pgettext_lazy

from .widgets import RichTextEditorWidget


class RichTextField(forms.CharField):
    """A field for rich text editor, providing backend sanitization."""

    widget = RichTextEditorWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_text = pgettext_lazy(
            'Help text in rich-text editor field',
            'Select text to enable text-formatting tools.')

    def to_python(self, value):
        tags = settings.ALLOWED_TAGS or bleach.ALLOWED_TAGS
        attributes = settings.ALLOWED_ATTRIBUTES or bleach.ALLOWED_ATTRIBUTES
        styles = settings.ALLOWED_STYLES or bleach.ALLOWED_STYLES
        value = super().to_python(value)
        value = bleach.clean(
            value, tags=tags, attributes=attributes, styles=styles)
        return value


class AjaxSelectMixin(object):
    def __init__(self, *args, **kwargs):
        super(AjaxSelectMixin, self).__init__(*args, **kwargs)

    def label_from_instance(self, node):
        """Creates labels which will represent each node when generating option labels."""
        if hasattr(node, '__str_staff__'):
            return getattr(node, '__str_staff__')
        return str(node)


class AjaxSelect2ChoiceField(AjaxSelectMixin, forms.ChoiceField):
    """An AJAX-based choice field using Select2.

    fetch_data_url - specifies url, from which select2 will fetch data
    initial - initial object
    """

    def __init__(self, fetch_data_url='', initial=None, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super().__init__(*args, **kwargs)
        self.widget.attrs['class'] = 'enable-ajax-select2'
        self.widget.attrs['data-url'] = fetch_data_url
        if initial:
            self.set_initial(initial)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            value = self.queryset.get(pk=value)
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            raise forms.ValidationError(
                self.error_messages['invalid_choice'], code='invalid_choice')
        return value

    def valid_value(self, value):
        forms.Field.validate(self, value)
        return True

    def set_initial(self, obj):
        """Set initially selected objects on field's widget."""
        selected = {'id': obj.pk, 'text': self.label_from_instance(obj)}
        self.widget.attrs['data-initial'] = json.dumps(selected)


class AjaxSelect2MultipleChoiceField(AjaxSelectMixin, forms.MultipleChoiceField):
    """An AJAX-base multiple choice field using Select2.

    fetch_data_url - specifies url, from which select2 will fetch data
    initial - list of initial objects
    """

    def __init__(self, fetch_data_url='', initial=[], *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super().__init__(*args, **kwargs)
        self.widget.attrs['class'] = 'enable-ajax-select2'
        self.widget.attrs['data-url'] = fetch_data_url
        if initial:
            self.set_initial(initial)
        self.widget.attrs['multiple'] = True

    def to_python(self, value):
        # Allow to set empty field
        if value == []:
            return value
        if value in self.empty_values:
            return None
        elif not isinstance(value, (list, tuple)):
            raise ValidationError(
                self.error_messages['invalid_list'], code='invalid_list')
        for choice in value:
            try:
                self.queryset.get(pk=choice)
            except (ValueError, TypeError, self.queryset.model.DoesNotExist):
                raise forms.ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice')
        return [str(val) for val in value]

    def valid_value(self, value):
        forms.Field.validate(self, value)
        return True

    def set_initial(self, objects):
        """Set initially selected objects on field's widget."""
        selected = [{'id': obj.pk, 'text': self.label_from_instance(obj)} for obj in objects]
        self.widget.attrs['data-initial'] = json.dumps(selected)
