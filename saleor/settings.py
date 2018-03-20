import ast
import os.path
import platform
from datetime import timedelta

import dj_database_url
import dj_email_url
from django.contrib.messages import constants as messages
import django_cache_url
from invoice_generator import models


def get_bool(name, default=False):
    if name in os.environ:
        value = os.environ[name]
        return ast.literal_eval(value)
    return default


def get_list(text):
    return [item.strip() for item in text.split(',')]


def env_get_list(key, default=None):
    res = []
    line = ''

    if key not in os.environ:
        return default

    text = os.environ[key]

    def _append():
        res.append(line)

    prev_char = None
    for c in text:
        if c == ';' and prev_char != '\\':
            _append()
            line = ''
        else:
            line += c
    _append()
    return res


def env_get_or_get(key, default_obj: dict, default_obj_key=None):
    res = os.environ.get(key, None)
    if not res:
        if default_obj_key is None:
            default_obj_key = key
        res = default_obj.get(default_obj_key, None)
    return res


if platform.python_implementation() == "PyPy":
    import psycopg2cffi.compat
    psycopg2cffi.compat.register()


DEBUG = get_bool('DEBUG', True)

SITE_ID = 1

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

ROOT_URLCONF = 'saleor.urls'

WSGI_APPLICATION = 'saleor.wsgi.application'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

INTERNAL_IPS = get_list(os.environ.get('INTERNAL_IPS', '127.0.0.1'))

CACHES = {'default': django_cache_url.config()}

if os.environ.get('REDIS_URL'):
    CACHES['default'] = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL')}

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://saleor:saleor@localhost:5432/biglight',
        conn_max_age=600)}

DEFAULT_TAX_RATE_COUNTRY = 'FR'
FALLBACK_TAX_RATE = 0.20

MAX_DELIVERY_DAYS = 21
MIN_DELIVERY_DAYS = 14

TIME_ZONE = 'Europe/Paris'
LANGUAGE_CODE = 'fr'
LOCALE_PATHS = [os.path.join(PROJECT_ROOT, 'locale')]
USE_I18N = True
USE_L10N = True
USE_TZ = True

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

EMAIL_URL = os.environ.get('EMAIL_URL')
SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
if not EMAIL_URL and SENDGRID_USERNAME and SENDGRID_PASSWORD:
    EMAIL_URL = 'smtp://%s:%s@smtp.sendgrid.net:587/?tls=True' % (
        SENDGRID_USERNAME, SENDGRID_PASSWORD)
email_config = dj_email_url.parse(EMAIL_URL or 'console://')

EMAIL_FILE_PATH = env_get_or_get('EMAIL_FILE_PATH', email_config)
EMAIL_HOST_USER = env_get_or_get('EMAIL_HOST_USER', email_config)
EMAIL_HOST_PASSWORD = env_get_or_get('EMAIL_HOST_PASSWORD', email_config)
EMAIL_HOST = env_get_or_get('EMAIL_HOST', email_config)
EMAIL_PORT = env_get_or_get('EMAIL_PORT', email_config)
EMAIL_BACKEND = env_get_or_get('EMAIL_BACKEND', email_config)
EMAIL_USE_TLS = env_get_or_get('EMAIL_USE_TLS', email_config)
EMAIL_USE_SSL = env_get_or_get('EMAIL_USE_SSL', email_config)

ENABLE_SSL = get_bool('ENABLE_SSL', False)

if ENABLE_SSL:
    SECURE_SSL_REDIRECT = True

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
ORDER_FROM_EMAIL = os.getenv('ORDER_FROM_EMAIL', DEFAULT_FROM_EMAIL)

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'

REAL_STATIC_ROOT = os.path.join(PROJECT_ROOT, 'saleor', 'static')

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    ('assets', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'assets')),
    ('images', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'images')),
    ('dashboard', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'dashboard'))]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder']

context_processors = [
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.i18n',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.template.context_processors.request',
    'saleor.core.context_processors.default_currency',
    'saleor.core.context_processors.categories',
    'saleor.cart.context_processors.cart_counter',
    'saleor.core.context_processors.search_enabled',
    'saleor.site.context_processors.site',
    'social_django.context_processors.backends',
    'social_django.context_processors.login_redirect']

loaders = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader']

if not DEBUG:
    loaders = [('django.template.loaders.cached.Loader', loaders)]

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
    'OPTIONS': {
        'debug': DEBUG,
        'context_processors': context_processors,
        'loaders': loaders,
        'string_if_invalid': '<< MISSING VARIABLE "%s" >>' if DEBUG else ''}}]

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY', 'secret')

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django_babel.middleware.LocaleMiddleware',
    'saleor.core.middleware.thread_request',
    'saleor.core.middleware.discounts',
    'saleor.core.middleware.google_analytics',
    'saleor.core.middleware.country',
    'saleor.core.middleware.currency',
    'saleor.core.middleware.site',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'impersonate.middleware.ImpersonateMiddleware']

INSTALLED_APPS = [
    # External apps that need to go before django's
    'storages',
    'invoice_generator.apps.InvoiceGeneratorConfig',
    'django_webhooking.apps.DjangoWebhooksConfig',

    # Django modules
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'django.contrib.postgres',
    'django.forms',

    # Local apps
    'saleor.userprofile',
    'saleor.discount',
    'saleor.product',
    'saleor.cart',
    'saleor.checkout',
    'saleor.core',
    'saleor.graphql',
    'saleor.order.OrderAppConfig',
    'saleor.dashboard',
    'saleor.shipping',
    'saleor.search',
    'saleor.site',
    'saleor.data_feeds',
    'saleor.page',

    # External apps
    'versatileimagefield',
    'django_babel',
    'bootstrap4',
    'django_fsm',
    'django_prices',
    'django_prices_openexchangerates',
    'graphene_django',
    'mptt',
    'payments',
    'webpack_loader',
    'social_django',
    'django_countries',
    'django_filters',
    'django_celery_results',
    'impersonate',
    'phonenumber_field']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['console']},
    'formatters': {
        'verbose': {
            'format': (
                '%(levelname)s %(name)s %(message)s'
                ' [PID:%(process)d:%(threadName)s]')},
        'simple': {
            'format': '%(levelname)s %(message)s'}},
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'}},
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'},
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'}},
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True},
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True},
        'saleor': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True}}}

AUTH_USER_MODEL = 'userprofile.User'

LOGIN_URL = '/account/login/'

DEFAULT_COUNTRY = 'FR'
DEFAULT_CURRENCY = 'EUR'
AVAILABLE_CURRENCIES = [DEFAULT_CURRENCY]

OPENEXCHANGERATES_API_KEY = os.environ.get('OPENEXCHANGERATES_API_KEY')

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = 'home'

GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get('GOOGLE_ANALYTICS_TRACKING_ID')


def get_host():
    from django.contrib.sites.models import Site
    return Site.objects.get_current().domain


PAYMENT_HOST = get_host

PAYMENT_MODEL = 'order.Payment'

PAYMENT_VARIANTS = {
}

CHECKOUT_PAYMENT_CHOICES = [
]


if 'PAYPAL_CLIENT_ID' in os.environ:
    PAYMENT_VARIANTS['paypal'] = ('payments.paypal.PaypalProvider', {
        'client_id': os.environ.get('PAYPAL_CLIENT_ID'),
        'secret': os.environ.get('PAYPAL_SECRET'),
        'endpoint': os.environ.get('PAYPAL_ENDPOINT', 'https://api.sandbox.paypal.com'),
        'capture': get_bool('PAYPAL_CAPTURE')
    })
    CHECKOUT_PAYMENT_CHOICES.append(('paypal', 'Paypal'))


if 'STRIPE_PUBLIC_KEY' in os.environ:
    PAYMENT_VARIANTS['stripe'] = ('payments.stripe.StripeProvider', {
        'public_key': os.environ.get('STRIPE_PUBLIC_KEY'),
        'secret_key': os.environ.get('STRIPE_SECRET_KEY'),
        'image': os.environ.get('STORE_IMAGE', ''),
        'name': os.environ.get('STORE_NAME', ''),
    })
    CHECKOUT_PAYMENT_CHOICES.append(('stripe', 'Stripe'))


if not CHECKOUT_PAYMENT_CHOICES or 'DUMMY_PROVIDER' in os.environ:
    PAYMENT_VARIANTS['default'] = ('payments.dummy.DummyProvider', {})
    CHECKOUT_PAYMENT_CHOICES.append(('default', 'Dummy provider'))


SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

MESSAGE_TAGS = {
    messages.ERROR: 'danger'}

LOW_STOCK_THRESHOLD = 10
MAX_CART_LINE_QUANTITY = int(os.environ.get('MAX_CART_LINE_QUANTITY', 50))

PAGINATE_BY = 16
DASHBOARD_PAGINATE_BY = 30
DASHBOARD_SEARCH_LIMIT = 5

bootstrap4 = {
    'set_placeholder': False,
    'set_required': False,
    'success_css_class': '',
    'form_renderers': {
        'default': 'saleor.core.utils.form_renderer.FormRenderer'}}

TEST_RUNNER = ''

ALLOWED_HOSTS = get_list(os.environ.get('ALLOWED_HOSTS', '127.0.0.1')) + ['demo.big-light.fr']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Amazon S3 configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_MEDIA_BUCKET_NAME = os.environ.get('AWS_MEDIA_BUCKET_NAME')
AWS_QUERYSTRING_AUTH = get_bool('AWS_QUERYSTRING_AUTH', False)

if AWS_STORAGE_BUCKET_NAME:
    if 'AWS_STATIC_CUSTOM_DOMAIN' in os.environ:
        AWS_S3_CUSTOM_DOMAIN = os.environ['AWS_STATIC_CUSTOM_DOMAIN']
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

if AWS_MEDIA_BUCKET_NAME:
    AWS_MEDIA_CUSTOM_DOMAIN = os.environ.get('AWS_MEDIA_CUSTOM_DOMAIN')
    DEFAULT_FILE_STORAGE = 'saleor.core.storages.S3MediaStorage'
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE
else:
    THUMBNAIL_DEFAULT_STORAGE = None

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'defaults': [
        ('product_gallery', 'fit__540x540'),
        ('product_gallery_2x', 'fit__1080x1080'),
        ('product_small', 'fit__60x60'),
        ('product_small_2x', 'fit__120x120'),
        ('product_list', 'fit__255x255'),
        ('product_list_2x', 'fit__510x510')]}

VERSATILEIMAGEFIELD_SETTINGS = {
    # Images should be pre-generated on Production environment
    'create_images_on_demand': get_bool('CREATE_IMAGES_ON_DEMAND', True)
}

PLACEHOLDER_IMAGES = {
    60: 'images/placeholder60x60.png',
    120: 'images/placeholder120x120.png',
    255: 'images/placeholder255x255.png',
    540: 'images/placeholder540x540.png',
    1080: 'images/placeholder1080x1080.png'}

DEFAULT_PLACEHOLDER = 'images/placeholder255x255.png'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'assets/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'webpack-bundle.json'),
        'POLL_INTERVAL': 0.1,
        'IGNORE': [
            r'.+\.hot-update\.js',
            r'.+\.map']}}


LOGOUT_ON_PASSWORD_CHANGE = False

# SEARCH CONFIGURATION
DB_SEARCH_ENABLED = True

# support deployment-dependant elastic enviroment variable
ES_URL = (os.environ.get('ELASTICSEARCH_URL') or
          os.environ.get('SEARCHBOX_URL') or os.environ.get('BONSAI_URL'))

ENABLE_SEARCH = bool(ES_URL) or DB_SEARCH_ENABLED  # global search disabling

SEARCH_BACKEND = 'saleor.search.backends.postgresql'

if ES_URL:
    SEARCH_BACKEND = 'saleor.search.backends.elasticsearch'
    INSTALLED_APPS.append('django_elasticsearch_dsl')
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': ES_URL}}


GRAPHENE = {
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware'],
    'SCHEMA': 'saleor.graphql.api.schema',
    'SCHEMA_OUTPUT': os.path.join(
        PROJECT_ROOT, 'saleor', 'static', 'schema.json')}

AUTHENTICATION_BACKENDS = [
    'saleor.registration.backends.facebook.CustomFacebookOAuth2',
    'saleor.registration.backends.google.CustomGoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend']

SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details']

SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, email'}

# CELERY SETTINGS
CELERY_BROKER_URL = os.environ.get('REDIS_BROKER_URL') or ''
CELERY_TASK_ALWAYS_EAGER = False if CELERY_BROKER_URL else True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'

# Impersonate module settings
IMPERSONATE = {
    'URI_EXCLUSIONS': [r'^dashboard/'],
    'CUSTOM_USER_QUERYSET': 'saleor.userprofile.impersonate.get_impersonatable_users',  # noqa
    'USE_HTTP_REFERER': True,
    'CUSTOM_ALLOW': 'saleor.userprofile.impersonate.can_impersonate'}

# Invoice data about the vendor
INVOICE_VENDOR_ADDRESS = models.Address(
    name=os.environ.get('INVOICE_VENDOR_NAME', 'Mirumee Software'),
    street=os.environ.get('INVOICE_VENDOR_STREET', 'Tęczowa 7'),
    postcode=os.environ.get('INVOICE_VENDOR_POSTCODE', '53-601'),
    city=os.environ.get('INVOICE_VENDOR_CITY', 'Wrocław'))

INVOICE_EXECUTIVE = (
    os.environ.get('INVOICE_EXECUTIVE_NAME', 'John Doe'),
    *env_get_list('INVOICE_EXECUTIVE_TEXT', tuple())
)

INVOICE_VENDOR = models.Vendor(
    executive_data=INVOICE_EXECUTIVE,
    address=INVOICE_VENDOR_ADDRESS,
    vat_number=os.environ.get('INVOICE_VAT_NUMBER', 'PL00000000000'),
    additional_text=env_get_list('INVOICE_VENDOR_ADDITIONAL_TEXT', tuple()))

INVOICE_ADDITIONAL_TEXT = env_get_list('INVOICE_ADDITIONAL_TEXT', tuple())

SIREN_CODE = os.environ.get('SIREN_CODE', 'SR_00')

WEBHOOK_HANDLERS = (
    (
        # Webhook Handler,  args,     events to push to it
        'DiscordWebhook',
        (os.environ.get('WEBHOOK_ORDER_DISCORD_URL'),),
        ('saleor.order.models.Order',
         'saleor.order.models.OrderNote',)
    ),
    (
        # Webhook Handler,  args,     events to push to it
        'DiscordWebhook',
        (os.environ.get('WEBHOOK_USER_DISCORD_URL'),),
        ('saleor.userprofile.models.User',)
    ),
)

CSRF_FAILURE_VIEW = 'saleor.core.views.csrf_failure'

# Rich-text editor
ALLOWED_TAGS = [
    'a',
    'b',
    'blockquote',
    'br',
    'em',
    'h2',
    'h3',
    'i',
    'img',
    'li',
    'ol',
    'p',
    'strong',
    'ul']
ALLOWED_ATTRIBUTES = {
    '*': ['align', 'style'],
    'a': ['href', 'title'],
    'img': ['src']}
ALLOWED_STYLES = ['text-align']

SOCIAL_LINKS_FACEBOOK = os.environ.get('SOCIAL_LINKS_FACEBOOK', 'mirumeelabs')
SOCIAL_LINKS_TWITTER = os.environ.get('SOCIAL_LINKS_TWITTER', 'getsaleor')
SOCIAL_LINKS_GOOGLE = os.environ.get('SOCIAL_LINKS_GOOGLE', '+Mirumee')
SOCIAL_LINKS_INSTAGRAM = os.environ.get('SOCIAL_LINKS_INSTAGRAM', 'explore/tags/mirumee/')

EMAIL_FOOTER_TEXT = os.environ.get('EMAIL_FOOTER_TEXT', '')
