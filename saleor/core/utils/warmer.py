from versatileimagefield.datastructures import SizedImage
from versatileimagefield.utils import get_resized_path

import logging

PRODUCT_IMAGE_SIZES = (60, 120, 255, 510, 540, 1080)
PRODUCT_IMAGE_SETS = [
    ('fit', '{0}x{0}'.format(size))
    for size in PRODUCT_IMAGE_SIZES
]


CATEGORY_IMAGE_SETS = (('crop', '400x400'), ('crop', '255x255'), ('crop', '120x120'))
HOMEPAGE_BLOCK_SETS = (('thumbnail', '1080x720'), )

logger = logging.getLogger(__name__)


def create_if_not_exists(image, method, size_key, check_existing=True):
    width, height = [int(i) for i in size_key.split('x')]
    method = getattr(image, method)  # type: SizedImage

    image_info = dict(
        path_to_image=method.path_to_image,
        width=width,
        height=height)

    resized_storage_path = get_resized_path(
        filename_key=method.get_filename_key(),
        storage=method.storage, **image_info
    )

    resized_url = method.storage.url(resized_storage_path)

    if check_existing and method.storage.exists(resized_storage_path):
        return None

    method.create_resized_image(
        save_path_on_storage=resized_storage_path, **image_info)

    return resized_url


class Warmer:
    def __init__(self, query_set, method_sets, attr):
        self.query_set = query_set
        self.sets = method_sets
        self.attr = attr

    def __call__(self, *args, **kwargs):
        created = 0
        for item in self.query_set:
            image = getattr(item, self.attr)
            if not image:
                continue

            for meth, size in self.sets:
                created_url = create_if_not_exists(image, meth, size)
                if created_url:
                    created += 1
                    logger.info(
                        'Created %s with %s & %s (%s)',
                        image, meth, size, created_url)
        return created


class ProductWarmer:
    def __init__(self, items):
        self._wrapper = Warmer(items, PRODUCT_IMAGE_SETS, 'image')

    @classmethod
    def all(cls):
        from saleor.product.models import ProductImage
        return cls(ProductImage.objects.all())

    def __call__(self, *args, **kwargs):
        return self._wrapper(*args, **kwargs)


class CategoryWarmer:
    def __init__(self, items):
        self._wrapper = Warmer(items, CATEGORY_IMAGE_SETS, 'image')

    @classmethod
    def all(cls):
        from saleor.product.models import Category
        return cls(Category.objects.all())

    def __call__(self, *args, **kwargs):
        return self._wrapper(*args, **kwargs)


class HomePageBlockWarmer:
    def __init__(self, items):
        self._wrapper = Warmer(items, HOMEPAGE_BLOCK_SETS, 'cover')

    @classmethod
    def all(cls):
        from saleor.homepage.models import HomePageItem
        return cls(HomePageItem.objects.all())

    def __call__(self, *args, **kwargs):
        return self._wrapper(*args, **kwargs)
