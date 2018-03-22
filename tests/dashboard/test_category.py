from unittest.mock import Mock, MagicMock, call
from django.urls import reverse

from saleor.core.utils import warmer
from saleor.product.models import Category

from ..utils import create_image

warmer.CategoryWarmer = MagicMock()
warmer.ProductWarmer = MagicMock()

warmer.create_if_not_exists = Mock(wraps=warmer.create_if_not_exists)


def _reset_mock_warmer(cls):
    cls.reset_mock()
    warmer.create_if_not_exists.reset_mock()


def test_category_list(admin_client, default_category):
    url = reverse('dashboard:category-list')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_category_add(admin_client):
    _reset_mock_warmer(warmer.CategoryWarmer)

    assert len(Category.objects.all()) == 0
    image, image_name = create_image()
    url = reverse('dashboard:category-add')
    data = {'name': 'Cars', 'description': 'Fastest cars', 'image': image}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(Category.objects.all()) == 1

    category = Category.objects.first()
    image = category.image

    assert image

    expected_calls = [
        call(image, meth, size) for meth, size in warmer.CATEGORY_IMAGE_SETS
    ]
    warmer.create_if_not_exists.assert_has_calls(expected_calls, True)


def test_category_add_not_valid(admin_client):
    assert len(Category.objects.all()) == 0
    url = reverse('dashboard:category-add')
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(Category.objects.all()) == 0


def test_category_add_subcategory(admin_client, default_category):
    assert len(Category.objects.all()) == 1
    url = reverse('dashboard:category-add',
                  kwargs={'root_pk': default_category.pk})
    data = {'name': 'Cars', 'description': 'Fastest cars'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(Category.objects.all()) == 2
    default_category.refresh_from_db()
    subcategories = default_category.get_children()
    assert len(subcategories) == 1
    assert subcategories[0].name == 'Cars'


def test_category_edit(admin_client, default_category):
    assert len(Category.objects.all()) == 1
    url = reverse('dashboard:category-edit',
                  kwargs={'root_pk': default_category.pk})
    data = {'name': 'Cars', 'description': 'Super fast!'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(Category.objects.all()) == 1
    assert Category.objects.all()[0].name == 'Cars'


def test_category_edit_image(admin_client, default_category):
    _reset_mock_warmer(warmer.CategoryWarmer)
    assert len(Category.objects.all()) == 1
    url = reverse('dashboard:category-edit',
                  kwargs={'root_pk': default_category.pk})
    data = {'name': 'Cars', 'description': 'Super fast!'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(Category.objects.all()) == 1
    assert Category.objects.all()[0].name == 'Cars'
    warmer.create_if_not_exists.assert_not_called()

    data = {'name': 'Cars', 'description': 'Super fast!', 'image': create_image()[0]}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    expected_calls = [
        call(Category.objects.first().image, meth, size)
        for meth, size in warmer.CATEGORY_IMAGE_SETS
    ]
    warmer.create_if_not_exists.assert_has_calls(expected_calls, True)


def test_category_move(admin_client, default_category):
    child_category = Category.objects.create(slug='child', name='child', parent=default_category)

    def _get_url(_pk):
        _url = reverse(
            'dashboard:category-move', kwargs={'root_pk': _pk})
        return _url

    def _test_post(_category, _data=None, _expected_code=302):
        _url = _get_url(_category.pk)
        _data = _data or {}
        _data.setdefault('position', 'first-child')

        _response = admin_client.post(_url, _data)
        _category = Category.objects.get(pk=_category.pk)

        assert _response.status_code == _expected_code
        return _category

    # set default category parent to children, should raise a 400
    category = _test_post(default_category, {'target': child_category.pk}, 400)
    assert category.parent is None

    # set default category parent to itself, should raise a 400
    category = _test_post(default_category, {'target': default_category.pk}, 400)
    assert category.parent is None

    # set child parent to default_category
    category = _test_post(child_category, {'target': default_category.pk})
    assert category.parent.pk == default_category.pk

    # set child parent to none (root)
    category = _test_post(child_category, {'target': ''}, 302)
    assert category.parent is None


def test_category_detail(admin_client, default_category):
    assert len(Category.objects.all()) == 1
    url = reverse('dashboard:category-detail',
                  kwargs={'pk': default_category.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200

    expected_url = '{}?category={}'.format(
        reverse('dashboard:product-list'), default_category.pk)

    assert 'href="%s">' % expected_url in response.content.decode('utf-8')
    response = admin_client.get(expected_url)
    assert response.status_code == 200


def test_category_delete(admin_client, default_category):
    assert len(Category.objects.all()) == 1
    url = reverse('dashboard:category-delete',
                  kwargs={'pk': default_category.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert len(Category.objects.all()) == 0
