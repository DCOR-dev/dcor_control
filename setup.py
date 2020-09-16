from os.path import exists, dirname, realpath
from setuptools import setup, find_packages
import sys

author = "Paul Müller"
authors = [author]
description = 'CLI for maintaining DCOR installations'
name = 'dcor_control'
year = "2020"

sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
try:
    from _version import version  # @UnresolvedImport
except BaseException:
    version = "unknown"


setup(
    name=name,
    author=author,
    author_email='dev@craban.de',
    url='https://github.com/DCOR-dev/dcor_control/',
    version=version,
    packages=find_packages(),
    package_dir={name: name},
    include_package_data=True,
    license="GPLv3+",
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    install_requires=[
        "appdirs",
        "ckan",
        "click>=7",
        "ckanext-dc_log_view",
        "ckanext-dc_serve",
        "ckanext-dc_view",
        "ckanext-dcor_depot",
        "ckanext-dcor_schemas",
        "ckanext-dcor_theme",
        "dcor_shared",
        # Additional dependencies by the DCOR extensions
        # (CKAN policy prohibits dependencies in setup.py)
        "dclab>=0.27.11",
        "matplotlib",  # dc_view
        "numpy>=1.19",  # dc_view
        "pillow",  # dc_view
        "html2text==2019.8.11",  # dcor_depot
        "requests",  # dcor_depot
        "python-slugify",  # dcor_schemas
        "Babel>=2.8.0",  # dcor_theme
        ],
    # not to be confused with definitions in pyproject.toml [build-system]
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    entry_points={
       "console_scripts": [
           "dcor = dcor_control.main:cli",
            ],
       },
    keywords=["RT-DC", "DCOR"],
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later ' \
        + '(GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Visualization',
        'Intended Audience :: Science/Research',
        ],
    )
