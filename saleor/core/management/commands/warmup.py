from django.core.management import BaseCommand
from saleor.core.utils.warmer import ProductWarmer, CategoryWarmer


class Command(BaseCommand):
    def handle(self, *args, **options):
        product_warmer = ProductWarmer.all()
        category_warmer = CategoryWarmer.all()

        for warmer in (product_warmer, category_warmer):
            num_created = warmer()
            print('Created: {}'.format(num_created))
