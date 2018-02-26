# usage: [HOST] [PORT]

import multiprocessing
import sys
import pwd
import os


def get_login():
    return pwd.getpwuid(os.getuid())[0]


def serialize(data: dict):
    config = '[uwsgi]\n'

    config += '\n'.join([
        '%s = %s' % i for i in data.items()
    ])

    return config


LOGIN_NAME = get_login()


def main(host=None, listener_guid=None, listener_uid=None, **overrides):
    host = host or '/tmp/uwsgi.sock'
    WORKERS = multiprocessing.cpu_count() * 2 + 1

    # GUID, UID
    LISTENER_GUID = listener_guid or 'http'
    LISTENER_UID = listener_uid or 'http'

    CHOWN_SOCKET = '%s:%s' % (LISTENER_GUID, LISTENER_GUID)

    UWSGI_CONFIG = {
        'workers': WORKERS,
        # 'threads': WORKERS,
        'socket': host,
        'max_requests': 30 * WORKERS,

        'gid': LISTENER_GUID,
        'uid': LISTENER_GUID,
        'listen.owner': LISTENER_UID,
        'listen.group': LISTENER_GUID,

        'logger': 'file:/tmp/errlog',

        'log-format': (
            'UWSGI uwsgi '
            '"%(method) %(uri) %(proto)" '
            '%(status) %(size) %(msecs)ms '
            '[PID:%(pid):Worker-%(wid)] '
            '[RSS:%(rssM)MB]'
        ),

        'die-on-term': True,
        'master': True,
        'module': 'saleor.wsgi:application',
        'static-map': '/static=/app/static',
        'thunder-lock': True
    }

    UWSGI_CONFIG.update(overrides)

    if host.startswith('/'):
        UWSGI_CONFIG['server'] = UWSGI_CONFIG['socket']

        if LOGIN_NAME == LISTENER_GUID:
            UWSGI_CONFIG['chown-socket'] = CHOWN_SOCKET

    return UWSGI_CONFIG


if __name__ == '__main__':
    HOST = os.environ.get('HOST', '/tmp/uwsgi.sock')
    output = main(HOST, 'www-data', 'www-data')
    sys.stdout.write(serialize(output))
