import datetime
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.contrib.postgres.fields import HStoreField
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Max, Q
from django.urls import reverse
from django.utils.encoding import smart_text
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy, gettext_lazy
from django_prices.models import Price, PriceField
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from prices import PriceRange
from satchless.item import InsufficientStock, Item, ItemRange
from text_unidecode import unidecode
from versatileimagefield.fields import PPOIField, VersatileImageField

from ..core.utils.warmer import ProductWarmer, CategoryWarmer
from ..discount.utils import calculate_discounted_price
from .utils import get_attributes_display_map


class Category(MPTTModel):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=50)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)

    objects = models.Manager()
    tree = TreeManager()

    image = VersatileImageField(upload_to='categories', blank=True)

    class Meta:
        app_label = 'product'
        permissions = (
            ('view_category',
             pgettext_lazy('Permission description', 'Can view categories')),
            ('edit_category',
             pgettext_lazy('Permission description', 'Can edit categories')))

    def __str__(self):
        return self.name

    @shared_task
    def create_category_thumbnails(self):
        CategoryWarmer(items=[self])()

    def get_absolute_url(self, ancestors=None):
        return reverse('product:category',
                       kwargs={'path': self.get_full_path(ancestors),
                               'category_id': self.id})

    def get_full_path(self, ancestors=None):
        if not self.parent_id:
            return self.slug
        if not ancestors:
            ancestors = self.get_ancestors()
        nodes = [node for node in ancestors] + [self]
        return '/'.join([node.slug for node in nodes])


class ProductType(models.Model):
    name = models.CharField(max_length=128)
    has_variants = models.BooleanField(default=True)
    product_attributes = models.ManyToManyField(
        'ProductAttribute', related_name='product_types', blank=True)
    variant_attributes = models.ManyToManyField(
        'ProductAttribute', related_name='product_variant_types', blank=True)
    is_shipping_required = models.BooleanField(default=False)

    class Meta:
        app_label = 'product'

    def __str__(self):
        return self.name

    def __repr__(self):
        class_ = type(self)
        return '<%s.%s(pk=%r, name=%r)>' % (
            class_.__module__, class_.__name__, self.pk, self.name)


class ProductQuerySet(models.QuerySet):
    def available_products(self):
        today = datetime.date.today()
        return self.filter(
            Q(available_on__lte=today) | Q(available_on__isnull=True),
            Q(is_published=True))


AVAILABILITY_MSG_FROM_TO = gettext_lazy(
    'This product is available within %(from)d to %(to)d days.')

AVAILABILITY_MSG_WITHIN = gettext_lazy(
    'This product is available within %(from)d days.')


class Product(models.Model, ItemRange):
    product_type = models.ForeignKey(
        ProductType, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    description = models.TextField()
    category = models.ForeignKey(
        Category, related_name='products', on_delete=models.CASCADE)
    price = PriceField(
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2)
    available_on = models.DateField(blank=True, null=True)
    is_published = models.BooleanField(default=True)
    attributes = HStoreField(default={})
    updated_at = models.DateTimeField(auto_now=True, null=True)
    is_featured = models.BooleanField(default=False)

    objects = ProductQuerySet.as_manager()

    class Meta:
        app_label = 'product'
        permissions = (
            ('view_product',
             pgettext_lazy('Permission description', 'Can view products')),
            ('edit_product',
             pgettext_lazy('Permission description', 'Can edit products')),
            ('view_properties',
             pgettext_lazy(
                 'Permission description', 'Can view product properties')),
            ('edit_properties',
             pgettext_lazy(
                 'Permission description', 'Can edit product properties')))

    def __iter__(self):
        if not hasattr(self, '__variants'):
            setattr(self, '__variants', self.variants.all())
        return iter(getattr(self, '__variants'))

    def __repr__(self):
        class_ = type(self)
        return '<%s.%s(pk=%r, name=%r)>' % (
            class_.__module__, class_.__name__, self.pk, self.name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'product:details',
            kwargs={'slug': self.get_slug(), 'product_id': self.id})

    def get_slug(self):
        return slugify(smart_text(unidecode(self.name)))

    def is_in_stock(self):
        return any(variant.is_in_stock() for variant in self)

    def is_available(self):
        today = datetime.date.today()
        return self.available_on is None or self.available_on <= today

    def get_first_image(self):
        first_image = self.images.first()
        return first_image.image if first_image else None

    def get_attribute(self, pk):
        return self.attributes.get(smart_text(pk))

    def set_attribute(self, pk, value_pk):
        self.attributes[smart_text(pk)] = smart_text(value_pk)

    def get_price_range(self, discounts=None, **kwargs):
        if self.variants.exists():
            return super().get_price_range(discounts=discounts, **kwargs)
        price = calculate_discounted_price(
            self, self.price, discounts, **kwargs)
        return PriceRange(price, price)

    def get_gross_price_range(self, **kwargs):
        grosses = [self.get_price_per_item(item, **kwargs) for item in self]
        if not grosses:
            return None
        grosses = sorted(grosses, key=lambda x: x.tax)
        return PriceRange(min(grosses), max(grosses))

    def _get_stocks(self):
        for variant in self.variants.all():
            for stock in variant.stock.all():
                yield stock

    def _get_availability(self):
        mins, maxs = [], []

        for stock in self._get_stocks():
            if stock.min_days:
                mins.append(stock.min_days)

            if stock.max_days:
                maxs.append(stock.max_days)

        return mins, maxs

    def _get_availability_range(self):
        mins, maxs = self._get_availability()
        min_days, max_days = 0, 0

        if mins:
            if len(mins) > 2:
                min_days = min(*mins)
            else:
                min_days = mins[0]
        if maxs:
            max_days = max(0, *maxs)

        return min_days, max_days

    def _format_availability(self):
        min_days, max_days = self._get_availability_range()

        is_from = min_days or max_days
        format_data = {'from': is_from, 'to': max_days}

        if is_from:
            if max_days and format_data['from'] != max_days:
                return AVAILABILITY_MSG_FROM_TO % format_data
            return AVAILABILITY_MSG_WITHIN % format_data
        return ''

    def get_availability_range(self):
        if self.variants.exists():
            return self._format_availability()
        return ''

    @property
    def availability_within_days(self):
        return self._get_availability_range()

    @property
    def availability_range(self):
        return self.get_availability_range()


class ProductVariant(models.Model, Item):
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100, blank=True)
    price_override = PriceField(
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)
    product = models.ForeignKey(
        Product, related_name='variants', on_delete=models.CASCADE)
    attributes = HStoreField(default={})
    images = models.ManyToManyField('ProductImage', through='VariantImage')

    class Meta:
        app_label = 'product'

    def __str__(self):
        return self.name or self.display_variant_attributes()

    def check_quantity(self, quantity):
        total_available_quantity = self.get_stock_quantity()
        if quantity > total_available_quantity:
            raise InsufficientStock(self)

    def get_stock_quantity(self):
        return sum([stock.quantity_available for stock in self.stock.all()])

    def get_price_per_item(self, discounts=None, **kwargs):
        price = self.price_override or self.product.price
        price = calculate_discounted_price(self.product, price, discounts,
                                           **kwargs)
        return price

    def get_absolute_url(self):
        slug = self.product.get_slug()
        product_id = self.product.id
        return reverse('product:details',
                       kwargs={'slug': slug, 'product_id': product_id})

    def as_data(self):
        return {
            'product_name': str(self),
            'product_id': self.product.pk,
            'variant_id': self.pk,
            'unit_price': str(self.get_price_per_item().gross)}

    def is_shipping_required(self):
        return self.product.product_type.is_shipping_required

    def is_in_stock(self):
        return any(
            [stock.quantity_available > 0 for stock in self.stock.all()])

    def get_attribute(self, pk):
        return self.attributes.get(smart_text(pk))

    def set_attribute(self, pk, value_pk):
        self.attributes[smart_text(pk)] = smart_text(value_pk)

    def display_variant_attributes(self, attributes=None):
        if attributes is None:
            attributes = self.product.product_type.variant_attributes.all()
        values = get_attributes_display_map(self, attributes)
        if values:
            return ', '.join(
                ['%s: %s' % (smart_text(attributes.get(id=int(key))),
                             smart_text(value))
                 for (key, value) in values.items()])
        return ''

    def display_product(self):
        variant_display = str(self)
        product_display = (
            '%s (%s)' % (self.product, variant_display)
            if variant_display else str(self.product))
        return smart_text(product_display)

    def get_first_image(self):
        return self.product.get_first_image()

    def select_stockrecord(self, quantity=1):
        # By default selects stock with lowest cost price. If stock cost price
        # is None we assume price equal to zero to allow sorting.
        stock = [
            stock_item for stock_item in self.stock.all()
            if stock_item.quantity_available >= quantity]
        zero_price = Price(0, currency=settings.DEFAULT_CURRENCY)
        stock = sorted(
            stock, key=(lambda s: s.cost_price or zero_price), reverse=False)
        if stock:
            return stock[0]
        return None

    def get_cost_price(self):
        stock = self.select_stockrecord()
        if stock:
            return stock.cost_price
        return None


class StockLocation(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        permissions = (
            ('view_stock_location',
             pgettext_lazy('Permission description',
                           'Can view stock location')),
            ('edit_stock_location',
             pgettext_lazy('Permission description',
                           'Can edit stock location')))

    def __str__(self):
        return self.name


class Stock(models.Model):
    variant = models.ForeignKey(
        ProductVariant, related_name='stock', on_delete=models.CASCADE)
    location = models.ForeignKey(
        StockLocation, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(1))
    quantity_allocated = models.IntegerField(
        validators=[MinValueValidator(0)], default=Decimal(0))
    cost_price = PriceField(
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)

    min_days = models.PositiveIntegerField(blank=True, null=True)
    max_days = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        app_label = 'product'
        unique_together = ('variant', 'location')

    def __str__(self):
        return '%s - %s' % (self.variant.name, self.location)

    @property
    def quantity_available(self):
        return max(self.quantity - self.quantity_allocated, 0)


class ProductAttribute(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    hidden = models.BooleanField(default=False, null=False)

    class Meta:
        ordering = ('slug', )

    def __str__(self):
        # debug purposes!
        # return '{0.name} ({0.slug})'.format(self)
        return self.name

    def get_formfield_name(self):
        return slugify('attribute-%s' % self.slug, allow_unicode=True)

    def has_values(self):
        return self.values.exists()


class AttributeChoiceValue(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    color = models.CharField(
        max_length=7, blank=True,
        validators=[RegexValidator('^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')])
    attribute = models.ForeignKey(
        ProductAttribute, related_name='values', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'attribute')

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name='images', on_delete=models.CASCADE)
    image = VersatileImageField(
        upload_to='products', ppoi_field='ppoi', blank=False)
    ppoi = PPOIField()
    alt = models.CharField(max_length=128, blank=True)
    order = models.PositiveIntegerField(editable=False)

    class Meta:
        ordering = ('order', )
        app_label = 'product'

    @shared_task
    def create_product_thumbnails(self):
        ProductWarmer(items=[self])()

    def get_ordering_queryset(self):
        return self.product.images.all()

    def save(self, *args, **kwargs):
        if self.order is None:
            qs = self.get_ordering_queryset()
            existing_max = qs.aggregate(Max('order'))
            existing_max = existing_max.get('order__max')
            self.order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        qs = self.get_ordering_queryset()
        qs.filter(order__gt=self.order).update(order=F('order') - 1)
        super().delete(*args, **kwargs)


class VariantImage(models.Model):
    variant = models.ForeignKey(
        'ProductVariant', related_name='variant_images',
        on_delete=models.CASCADE)
    image = models.ForeignKey(
        ProductImage, related_name='variant_images', on_delete=models.CASCADE)


class Collection(models.Model):
    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=255)
    products = models.ManyToManyField(
        Product, blank=True, related_name='collections')

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'product:collection',
            kwargs={'pk': self.id, 'slug': self.slug})
