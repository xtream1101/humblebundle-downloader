from setuptools import setup
from humblebundle_downloader._version import __version__


with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='humblebundle-downloader',
    packages=['humblebundle_downloader'],
    version=__version__,
    description='Download your Humble Bundle library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Eddy Hintze',
    author_email="eddy@hintze.co",
    url="https://github.com/xtream1101/humblebundle-downloader",
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'hbd=humblebundle_downloader.cli:cli',
        ],
    },
    install_requires=[
        'requests',
        'parsel',
        'selenium',
        'webdriverdownloader',
    ],

)
