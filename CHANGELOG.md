# Change log


### 0.3.1
- Added support for netscape cookies
 

### 0.3.0
- pip install now requires python version 3.4+
- `--trove` will only download trove products, nothing else
- Filtering flags now work when downloading trove content


### 0.2.2
- Confirm the download is complete by checking the expected size to what downloaded
- Fixed the platform filter


### 0.2.1
- Fixed include & exclude logic being switched in v0.2.0


### 0.2.0
- Added **Humble Trove** support _(`--trove` to also check/download trove content)_
- Now by default only new content is downloaded. Use `--update` to also check for updated content


### 0.1.3
- Fixed re-downloading for real this time
  - Only use the url last modified time as the check for new versions


### 0.1.2
- Stop using md5 & sha1 hashes to check if file is unique (was creating duplicate downloads of the same file)
- Strip periods from end of directory & file names
- Rename older versions of a file before download the new one


### 0.1.1
- Delete failed downloaded files
 

### 0.1.0
- Filename saved is now the original name of the file
- key used in cache is different due to changing the file name (this may result in duplicate downloads if you have run the older version)
- Support for downloading a single Bundle/Purchase by using the flag `-k` or `--key` and getting the key from the url of a purchase


### 0.0.8
- gen-cookies now works with SSO feature and 2FA logins
- Added `--include` & `--exclude` cli args to filter file types


### 0.0.7
- Replace `:` with ` -` in filenames
- Ignore items that do not have a web url


### 0.0.6
- Started change log
- Added more detail to readme
- Removed the use of f-strings to support more python versions
- Fixed bug where folders and files were only a single letter
