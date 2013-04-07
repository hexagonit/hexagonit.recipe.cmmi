from setuptools import setup, find_packages
import os

version = '2.0'
name = 'hexagonit.recipe.cmmi'


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name=name,
    version=version,
    description="zc.buildout recipe for compiling and installing source distributions.",
    long_description=(
        read('README.rst')
        + '\n' +
        read('CHANGES.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('hexagonit', 'recipe', 'cmmi', 'README.txt')
        + '\n' +
        'Download\n'
        '***********************\n'
    ),
    classifiers=[
        'Framework :: Buildout :: Recipe',
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='development buildout recipe',
    author='Kai Lautaportti',
    author_email='kai.lautaportti@hexagonit.fi',
    url='http://github.com/hexagonit/hexagonit.recipe.cmmi',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['hexagonit', 'hexagonit.recipe'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'zc.buildout',
        'setuptools',
        'hexagonit.recipe.download',
    ],
    extras_require={
        'test': ['zope.testing'],
    },
    tests_require=['zope.testing'],
    test_suite='hexagonit.recipe.cmmi.tests.test_suite',
    entry_points={'zc.buildout': ['default = hexagonit.recipe.cmmi:Recipe']},
)
