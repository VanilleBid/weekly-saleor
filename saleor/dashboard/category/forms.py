from django import forms
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from text_unidecode import unidecode
from mptt.forms import MoveNodeForm, TreeNodeChoiceField, TreeNodePositionField

from ...product.models import Category


LABEL_MOVE_CATEGORY_TARGET = pgettext_lazy('Move category form field: parent to set to category', 'Target')
LABEL_MOVE_CATEGORY_POSITION = pgettext_lazy('Move category form field: parent to set to category', 'Position')


class MoveCategoryForm(MoveNodeForm):
    # FIXME: i8ln is not working here (not extracting); no idea why.
    target = TreeNodeChoiceField(label=LABEL_MOVE_CATEGORY_TARGET, queryset=None, required=False)
    position = TreeNodePositionField(label=LABEL_MOVE_CATEGORY_POSITION)


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
