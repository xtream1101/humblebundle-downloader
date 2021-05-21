# Humble Bundle Downloader
[![PyPI](https://img.shields.io/pypi/v/humblebundle-downloader.svg)](https://pypi.python.org/pypi/humblebundle-downloader)
[![PyPI](https://img.shields.io/pypi/l/humblebundle-downloader.svg)](https://pypi.python.org/pypi/humblebundle-downloader)  


**Download all of your content from your Humble Bundle Library!**  

The first time this runs it may take a while because it will download everything. After that it will only download the content that has been updated or is missing.  

## Features
- support for Humble Trove _(`--trove` flag)_
- downloads new and updated content from your Humble Bundle Library on each run _(only check for updates if using `--update`)_
- cli command for easy use (downloading will also work on a headless system)
- works for SSO and 2FA accounts
- optional progress bar for each item downloaded _(`--progress` flag)_
- optional filter by file types using an include _or_ exclude list _(`--include/--exclude` flag)_
- optional filter by platform types like video, ebook, etc... _(`--platform` flag)_


## Install
`pip install humblebundle-downloader`


## Instructions

### 1. Getting cookies
First thing to do is get your account cookies. This can be done by getting a browser extension that lets you see or export your cookies.

- **Method 1 (recommended)**
    - Get the value of the cookie called `_simpleauth_sess` and pass that value using `-s "COOKIE_VALUE"`

- **Method 2**
    - Export the cookies in the Netscape format using an extension.  
    If your exported cookie file is not working, it may be a formatting issue, this can be fixed by running the command `curl -b cookies.orig.txt --cookie-jar cookies.txt http://bogus`


### 2. Downloading your library
Use the following command to download your Humble Bundle Library:  
`hbd --cookie-file cookies.txt --library-path "Downloaded Library" --progress`  

This directory structure will be used:  
`Downloaded Library/Purchase Name/Item Name/downloaded_file.ext`


## Notes
* Inside your library folder a file named `.cache.json` is saved and keeps track of the files that have been downloaded. This way running the download command again pointing to the same directory will only download new or updated files.
* Use `--help` with all `hbd` commands to see available options
* Find supported platforms for the `--platform` flag by visiting your Humble Bundle Library and look under the **Platform** dropdown
* Download select bundles by using the `-k` or `--keys` flag. Find these keys by going to your *Purchases* section, click on a products and there should be a `downloads?key=XXXX` in the url.
