# Humble Bundle Downloader
[![PyPI](https://img.shields.io/pypi/v/humblebundle-downloader.svg)](https://pypi.python.org/pypi/humblebundle-downloader)
[![PyPI](https://img.shields.io/pypi/l/humblebundle-downloader.svg)](https://pypi.python.org/pypi/humblebundle-downloader)  


Download all of you content from your Humble Bundle Library.  

The very first time this runs it may take a while to download everything, but after that it will only download the content that is missing.  

## Features
- Download new or updated content in your Library
- cli command for easy use
- Progress bar for each download _(with the `--progress` flag)_
- Easy cookie generation so script


## Install
`pip install humblebundle-downloader`


## Getting started
First thing to do is generate cookies, this will open up a chrome window, just login and a cookie will be saved to a file to be used later to download the files.  
`hbd gen-cookies -h`  

Now download your library:  
`hbd download -h`  

Inside your library folder a file called `.cache.json` is saved and keeps track of the files that have been downloaded, so running the download command pointing to the same directory will only download new files or update files if needed.
