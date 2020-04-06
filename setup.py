#!/usr/bin/env python
import os
import re
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', 'Arguments to pass to pytest')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests>=2.7.0',
    'lxml>=3.4.4'
]

test_requirements = [
    'pytest>=4.6.3',
    'pytest-cov>=2.7.1',
    'freezegun>=0.3.12',
    'vcrpy>=2.0.1'
]

setup(
    name='litresapi',
    version=get_version('litresapi'),
    description='Litres API',
    long_description=readme + '\n\n' + history,
    author='MyBook',
    author_email='dev@mybook.ru',
    url='https://github.com/MyBook/litresapi',
    packages=['litresapi'],
    package_dir={'litresapi': 'litresapi'},
    include_package_data=True,
    install_requires=requirements,
    license='BSD',
    zip_safe=False,
    keywords='litresapi',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    cmdclass={'test': PyTest},
)
