import warnings
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

try:
    # Make sure this fails for old CKAN versions
    import ckan
    ckan_version = [int(v) for v in ckan.__version__.split(".")]
    if ckan_version < [2, 10, 1]:
        raise ValueError(
            f"Your CKAN version {ckan_version} is not supported! If you "
            f"are still on CKAN 2.9.5, then the following package versions "
            f"are supported:"
            f"\n ckanext-dc_log_view<=0.2.9"
            f"\n ckanext-dc_serve<=0.11.1"
            f"\n ckanext-dc_view<=0.6.10"
            f"\n ckanext-dcor_depot<=0.11.0"
            f"\n ckanext-dcor_schemas<=0.17.2"
            f"\n ckanext-dcor_theme<=0.6.1"
            f"\n dcor_shared<=0.3.1"
            )
except ImportError:
    warnings.warn("CKAN not installed, supported version check skipped.")

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
        # the "ckan" dependency is implied
        "appdirs",
        "click>=7",
        "cryptography>=41",  # client beaker session cookies
        "ckanext-dc_log_view>0.2.9",
        "ckanext-dc_serve>0.11.1",
        "ckanext-dc_view>0.6.10",
        "ckanext-dcor_depot>0.11.0",
        "ckanext-dcor_schemas>0.17.2",
        "ckanext-dcor_theme>0.6.1",
        "dcor_shared>=0.5.2",
        "importlib_resources",
        "numpy>=1.21",  # CVE-2021-33430
        ],
    # not to be confused with definitions in pyproject.toml [build-system]
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    entry_points={
       "console_scripts": [
           "dcor = dcor_control.cli:main",
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
