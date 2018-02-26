import os
import os.path
import shutil

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management import BaseCommand

from saleor.dashboard.product.forms import ProductImageForm, UploadImageForm
from saleor.product.models import Product, ProductVariant, ProductImage


BASE_DIR = 'raw_data/thumbnails/'


def get_thumbs(path):
    res = {}
    files = sorted(os.listdir(path), reverse=True)

    for f in files:
        f_upper = f.upper()
        ref = ''

        for pos, char in enumerate(f_upper):
            if char in '.,_ ':
                break
            ref += char

        ref = ref.strip('-')
        res.setdefault(ref, []).append(f)

    return res


def get_products_by_ref():
    for product in Product.objects.all():
        variant = product.variants.first()  # type: ProductVariant

        if not variant:
            raise ValueError('For id = {}'.format(product.id))

        pic = product.images.first()  # type: ProductImage

        yield variant.sku.upper(), product.id, product


class Command(BaseCommand):
    help = 'Populate database with test objects'
    placeholders_dir = r'saleor/static/placeholders/'

    def handle(self, *args, **options):
        pic_dir = BASE_DIR + 'pics'
        thumbs = get_thumbs(pic_dir)

        output_dir = BASE_DIR + 'out'

        for ref, idx, product in get_products_by_ref():
            files = None
            for f_ref in thumbs:
                if ref[:len(f_ref)] == f_ref:
                    files = thumbs[f_ref]
                    break

            if not files:
                continue

            images = {}
            fd_list = []

            i = 0
            for f in files:
                f = os.path.join(pic_dir, f)

                fp = open(f, 'rb')
                fd_list.append(fp)

                pic = Image.open(fp)  # type: Image.Image
                content_type = Image.MIME[pic.format]

                field_name = 'image_%d' % i

                images[field_name] = \
                    InMemoryUploadedFile(
                        fp,
                        name='%d-%d.%s' % (idx, i, pic.format),
                        field_name=field_name,
                        content_type=content_type,
                        size=fp.tell(),
                        charset=None
                    )

                shutil.copy(f, os.path.join(output_dir, str(idx) + '.jpg'))
                i += 1

            for image in product.images.all():
                image.delete()

            for name, image in images.items():
                form = UploadImageForm(None, {'image_0': image}, product=product)

                if not form.is_valid():
                    print(form.errors)
                    raise AssertionError

                form.save()

            for fp in fd_list:
                fp.close()
