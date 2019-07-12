"""Setup file for the Skyflash tool"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='skyflash',
    version="0.0.4",
    description='Skycoin Skyminer\'s OS configuring and flashing',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/skycoin/skyflash',
    author='stdevPavelmc',
    author_email='pavelmc@gmail.com',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Betha',

        # Indicate who your project is intended for
        'Intended Audience :: Users',
        'Topic :: Tools :: Config & Flashing Tools',

        # Pick your license as you wish
        'License :: GNU :: GPL 2.0',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # These classifiers are *not* checked by 'pip install'. See instead
        # 'python_requires' below.
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # separated by whitespace, not a list.
    keywords='skycoin skyminer skybian flashing configuring',

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Specify which Python versions you support.
    python_requires='>=3.5.*, <4',

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    # install_requires=['python3-pyqt5'],

    # To provide executable scripts, in this case a gui app
    entry_points={
        'gui_scripts': [
            'skyflash-gui = skyflash:app',
        ]
    },

    # List additional URLs that are relevant to your project as a dict.
    project_urls={
        'Source': 'https://github.com/skycoin/skyflash/',
    },

    data_files={
        ('share/applications', (
            'skyflash/data/skyflash.desktop',
        )),
        ('share/icons', (
            'skyflash/data/skyflash.png',
        )),
        ('share/skyflash', (
            'skyflash/data/skyflash.qml',
        )),
        ('bin', (
            'skyflash/data/skyflash-cli',
        )),
    },
)
