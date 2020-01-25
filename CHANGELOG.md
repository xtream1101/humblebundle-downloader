# Change log


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
