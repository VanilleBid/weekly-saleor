from saleor.wsgi import uwsgi_config
from tests.utils import SetValue


def test_wsgi_config_unix_socket():
    socket = '/tmp/uwsgi_socket.sock'
    config = uwsgi_config.main(socket)
    assert socket in config['socket']
    assert socket in config['server']


def test_wsgi_config_unix_socket_chown():
    socket = '/tmp/uwsgi_socket.sock'

    with SetValue(uwsgi_config, 'LOGIN_NAME', 'nginx'):
        config = uwsgi_config.main(socket, 'nginx', 'http')
        assert config['chown-socket'] == 'nginx:http'

    with SetValue(uwsgi_config, 'LOGIN_NAME', 'user'):
        config = uwsgi_config.main(socket, 'nginx', 'http')
        assert 'chown-socket' not in config


def test_wsgi_config_http():
    socket = ':9000'
    config = uwsgi_config.main(socket)
    assert socket in config['socket']
    assert 'server' not in config
