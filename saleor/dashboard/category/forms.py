from django import forms
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from text_unidecode import unidecode
from mptt.forms import MoveNodeForm, TreeNodeChoiceField, TreeNodePositionField

from ...product.models import Category


class MoveCategoryForm(MoveNodeForm):
    target = TreeNodeChoiceField(
        label=pgettext_lazy('Move category form field: parent to set to category', 'Target'),
        queryset=None, required=False)
    position = TreeNodePositionField(
        label=pgettext_lazy(
            'Move category form field: position of the category in parent children', 'Position'))


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.parent_pk = kwargs.pop('parent_pk')
        super(CategoryForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Category
        exclude = ['slug']
        labels = {
            'name': pgettext_lazy(
                'Item name',
                'Name'),
            'description': pgettext_lazy(
                'Description',
                'Description'),
            'image': pgettext_lazy('Image', 'Image')}

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        if self.parent_pk:
            self.instance.parent = get_object_or_404(
                Category, pk=self.parent_pk)

        instance = super().save(commit=commit)
        if 'image' in self.changed_data:
            self.instance.create_category_thumbnails()

        return instance
