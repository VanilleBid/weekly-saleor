import os.path
from pkg_resources import parse_requirements
from setuptools import setup, find_packages
from sys import version_info


if not version_info > (3, 3):
    raise Exception(
        'This project requires a Python version greater or equal than 3.4.')


HERE = os.path.dirname(__file__)

with open(os.path.join(HERE, 'requirements.txt')) as fp:
    REQUIREMENTS = tuple(map(
        str, parse_requirements(fp.readlines())
    ))


setup(
    version='2018.1.4',
    name='saleor',
    author='Mirumee Software',
    author_email='hello@mirumee.com',
    url='https://github.com/mirumee/saleor',

    packages=find_packages(exclude=['tests']),
    data_files=(('', 'requirements.txt'),),
    keywords=tuple(),

    install_requires=REQUIREMENTS,

    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only'
    ],
)
