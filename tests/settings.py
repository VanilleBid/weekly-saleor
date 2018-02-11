# pylint: disable=W0401, W0614
from saleor.settings import *  # noqa

SECRET_KEY = 'NOTREALLY'

DEFAULT_CURRENCY = 'USD'

LANGUAGE_CODE = 'en-us'

if 'sqlite' in DATABASES['default']['ENGINE']:  # noqa
    DATABASES['default']['TEST'] = {  # noqa
        'SERIALIZE': False,
        'NAME': ':memory:',
        'MIRROR': None}
else:
    DATABASES = {
        'default': dj_database_url.config(
            default='postgres://saleor:saleor@localhost:5432/saleor',
            conn_max_age=600)}
