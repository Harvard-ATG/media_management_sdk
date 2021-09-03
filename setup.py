import os
from setuptools import setup
from setuptools import find_packages


with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as v_file:
    VERSION = v_file.read().strip()

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as r_file:
    README = r_file.read().strip()


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='media-management-sdk',
    version=VERSION,
    url="https://github.com/Harvard-ATG/media_management_sdk",
    description='A python SDK for the Image Media Manager API.',
    long_description=README,
    long_description_content_type="text/markdown",
    license="License :: OSI Approved :: BSD License",
    packages=find_packages(),
    install_requires=['requests', 'PyJWT>=1.7.1'],
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
