from django_positions_2 import *
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils.translation import pgettext_lazy
from versatileimagefield.fields import VersatileImageField

from ..core.templatetags.placeholder import placeholder
from ..core.utils.warmer import HomePageBlockWarmer
from ..page.models import Page
from ..product.models import Category, Collection


DEFAULT_PRIMARY_BTN_TEXT = pgettext_lazy("Homepage action", "Shop now")
DEFAULT_HTML_CLASSES = 'col-sm-12 col-md-6'


class HomePageItem(models.Model):
    title = models.CharField(
        max_length=100, validators=[MaxLengthValidator(100)],
        blank=False, null=False)
    subtitle = models.CharField(
        max_length=255, validators=[MaxLengthValidator(255)],
        blank=True, null=True)
    html_classes = models.CharField(
        max_length=100, validators=[MaxLengthValidator(100)],
        blank=True, null=False, default=DEFAULT_HTML_CLASSES)
    primary_button_text = models.CharField(
        max_length=100, validators=[MaxLengthValidator(100)],
        blank=True, null=True)

    cover = VersatileImageField(upload_to='homepage_blocks', blank=True)

    category = models.ForeignKey(
        Category, blank=True, null=True, on_delete=models.CASCADE)
    collection = models.ForeignKey(
        Collection, blank=True, null=True, on_delete=models.CASCADE)
    page = models.ForeignKey(
        Page, blank=True, null=True, on_delete=models.CASCADE)

    position = PositionField(blank=True)
    objects = PositionManager('position')

    class Meta:
        ordering = ('position', )
        permissions = (
            ('view_blocks_config',
             pgettext_lazy('Permission description', 'Can view home page configuration')),
            ('edit_blocks_config',
             pgettext_lazy('Permission description', 'Can edit home page configuration')))

    @property
    def cover_url(self):
        if self.cover:
            return self.cover.thumbnail['1080x720'].url
        return placeholder(540)

    @property
    def linked_object(self):
        return self.category or self.collection or self.page

    @property
    def primary_button(self):
        return self.primary_button_text or DEFAULT_PRIMARY_BTN_TEXT

    @property
    def url(self):
        linked_object = self.linked_object
        if linked_object:
            return linked_object.get_absolute_url()
        return '#'  # this case should only happen if relations were removed

    def create_thumbnails(self):
        HomePageBlockWarmer(items=[self])()
