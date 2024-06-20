# -*- coding: ascii -*-
"""
package/install module package udm-directory-connector
"""

import sys
import os
from setuptools import setup, find_packages

PYPI_NAME = 'udm-directory-connector'

BASEDIR = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, os.path.join(BASEDIR, 'udm_directory_connector'))
import __about__

setup(
    name=PYPI_NAME,
    license=__about__.__license__,
    version=__about__.__version__,
    description='UDM connector for LDAP source directories',
    author=__about__.__author__,
    author_email=__about__.__mail__,
    maintainer=__about__.__author__,
    maintainer_email=__about__.__mail__,
    url='https://git.knut.univention.de:univention/nubus/udm-directory-connector',
    keywords=[],
    packages=find_packages(exclude=['tests']),
    package_dir={'': '.'},
    test_suite='tests',
    python_requires='>=3.7.*',
    include_package_data=True,
    data_files=[],
    install_requires=[
        'setuptools',
        'certifi',
        'junkaptor >= 0.0.5',
        'phonenumbers',
        'python-ldap',
        'requests',
        'strictyaml',
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'udm-directory-connector = udm_directory_connector.__main__:cli',
        ],
    }
)
