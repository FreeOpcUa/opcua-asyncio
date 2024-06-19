from setuptools import setup, find_packages
import sys

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# don't require pytest-runner unless we have been invoked as a test launch
needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

setup(
    name="asyncua",
    version="1.1.0",
    description="Pure Python OPC-UA client and server library",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Olivier Roulet-Dubonnet",
    author_email="olivier.roulet@gmail.com",
    url='http://freeopcua.github.io/',
    packages=find_packages(exclude=["tests"]),
    provides=["asyncua"],
    license="GNU Lesser General Public License v3 or later",
    install_requires=["aiofiles", "aiosqlite", "python-dateutil", "pytz", "cryptography>42.0.0", "sortedcontainers", "importlib-metadata;python_version<'3.8'", "pyOpenSSL>23.2.0", "typing-extensions"],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        'console_scripts': [
            'uaread = asyncua.tools:uaread',
            'uals = asyncua.tools:uals',
            'uabrowse = asyncua.tools:uals',
            'uawrite = asyncua.tools:uawrite',
            'uasubscribe = asyncua.tools:uasubscribe',
            'uahistoryread = asyncua.tools:uahistoryread',
            'uaclient = asyncua.tools:uaclient',
            'uaserver = asyncua.tools:uaserver',
            'uadiscover = asyncua.tools:uadiscover',
            'uacall = asyncua.tools:uacall',
            'uageneratestructs = asyncua.tools:uageneratestructs',
        ]
    },
    setup_requires=[] + pytest_runner,
    tests_require=['pytest', 'pytest-mock', 'asynctest'],
)
