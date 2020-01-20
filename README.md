# Humble Bundle Downloader
[![PyPI](https://img.shields.io/pypi/v/humblebundle-downloader.svg)](https://pypi.python.org/pypi/humblebundle-downloader)
[![PyPI](https://img.shields.io/pypi/l/humblebundle-downloader.svg)](https://pypi.python.org/pypi/humblebundle-downloader)  


**Download all of your content from your Humble Bundle Library!**  

The first time this runs it may take a while because it will download everything. After that it will only download the content that has been updated or is missing.  

## Features
- downloads new and updated content from your Humble Bundle Library on each run
- cli command for easy use (downloading will also work on a headless system)
- works for SSO and 2FA accounts
- optional progress bar for each item downloaded _(`--progress` flag)_
- optional cookie generation script
- optional filter by file types using an include _or_ exclude list _(`--include/--exclude` flag)_
- optional filter by platform types like video, ebook, etc... _(`--platform` flag)_


## Install
`pip install humblebundle-downloader`


## Instructions

### 1. Getting cookies
First thing to do is get your account cookies, they will be used later to download the files.  
There are 2 ways to get your cookies: manual or scripted.  

#### Method 1: Manual
Use this method if you know how to get cookies from your browser after you are logged in.  
Once you have your cookies, save them to a text file named `hbd-cookies.txt` in this format:  
`hbflash=None;_fbp=fb.1.000000.000000;__ssid=XXXXXXXX;_gat=1;_gid=GA1.2.1111111.11111111;hbreqsec=True;_ga=GA1.2.1111111.111111;_simpleauth_sess=XXXXXXXXXXXXX;csrf_cookie=XXXXXXXXX`

#### Method 2: Scripted
**WARNING: This method may not work on all systems!**  
Requires: Chrome and a desktop-like environment (not headless).  

Run the command below to open a chrome window. After you login, the cookies will automatically be saved to a text file and the window will close.  
`hbd gen-cookies --cookie-file hbd-cookies.txt`  

### 2. Downloading your library
Use the following command to download your Humble Bundle Library:  
`hbd download --cookie-file hbd-cookies.txt --library-path "Downloaded Library" --progress`  

This directory structure will be used:  
`Downloaded Library/Purchase Name/Item Name/downloaded_file.ext`


## Notes
* Inside your library folder a file named `.cache.json` is saved and keeps track of the files that have been downloaded. This way running the download command again pointing to the same directory will only download new or updated files.
* Use `--help` with all `hbd` commands to see available options
* Find supported platforms for the `--platform` flag by visiting your Humble Bundle Library and look under the **Platform** dropdown
* Download select bundles by using the `-k` or `--keys` flag. Find these keys by going to your *Purchases* section, click on a products and there should be a `downloads?key=XXXX` in the url.
