import os
import sys
import logging
import argparse
from humblebundle_downloader._version import __version__

logger = logging.getLogger(__name__)

LOG_LEVEL = os.environ.get('HBD_LOGLEVEL', 'INFO').upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(message)s',
)
# Ignore unwanted logs from the requests lib when debuging
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

# convert a string representing size to an integer 
def parse_size(size):
    # Base10 unit definitions  
    # K=x1000  M=x10000000  G=x1000000000
    # units = {"K": 10**3, "M": 10**6, "G": 10**9, "T": 10**12}
    # Binary unit definitions:
    # K=x1024  M=x1024x1024 etc
    units = {"K": 2**10, "M": 2**20, "G": 2**30, "T": 2**40}
    try:
        return int(size)    # if it's an int already just return it
    except ValueError:  # it wasn't an int
        size=size.upper()
        if size.endswith('B'):
            return parse_size(size[:-1])
        unit=size[-1:]
        number=size[:-1]
        if unit not in units.keys():
            raise ValueError(f'Invalid Unit: {unit}')
        return int(float(number)*units[unit])

# convert a string represting time to an integer number of seconds
def parse_seconds(size):
    # convert parameter to number of seconds
    units = {"S": 1, "M": 60, "H": 60*60, "D": 60*60*24, 'W': 60*60*24*7}
    try:
        return int(size)    # if it's an int already just return it
    except ValueError:  # it wasn't an int
        size=size.upper()
        unit=size[-1:]
        number=size[:-1]
        if unit not in units.keys():
            raise ValueError(f'Invalid Unit: {unit}')
        return int(float(number)*units[unit])

def parse_args(args):
    if ((len(args)>0) and (args[0].lower() == 'download')):
        args = args[1:]
        raise DeprecationWarning("`download` argument is no longer used")

    parser = argparse.ArgumentParser(description='Download purchases from Humble Bundle',
        epilog=f'Version: {__version__}')

    cookie = parser.add_mutually_exclusive_group(required=True)
    cookie.add_argument(
        '-c', '--cookie-file', type=str,
        help="Location of the cookies file",
    )
    cookie.add_argument(
        '-s', '--session-auth', type=str,
        help="Value of the cookie _simpleauth_sess. WRAP IN QUOTES",
    )
    parser.add_argument(
        '-l', '--library-path', type=str,
        help="Folder to download all content to",
        required=True,
    )
    parser.add_argument(
        '-t', '--trove', action='store_true',
        help="Only check and download Humble Trove content",
    )
    parser.add_argument(
        '-u', '--update', action='store_true',
        help=("Check to see if products have been updated "
              "(still get new products)"),
    )
    parser.add_argument(
        '-p', '--platform',
        type=str, nargs='*',
        help=("Only get content in a platform. Values can be seen in your "
              "humble bundle's library dropdown. Ex: -p ebook video"),
    )
    parser.add_argument(
        '--progress',
        action='store_true',
        help="Display progress bar for downloads",
    )
    filter_ext = parser.add_mutually_exclusive_group()
    filter_ext.add_argument(
        '-e', '--exclude',
        type=str, nargs='*',
        help=("File extensions to ignore when downloading files. "
              "Ex: -e pdf mobi"),
    )
    filter_ext.add_argument(
        '-i', '--include',
        type=str, nargs='*',
        help="Only download files with these extensions. Ex: -i pdf mobi",
    )
    parser.add_argument(
        '-k', '--keys',
        type=str, nargs='*',
        help=("The purchase download key. Find in the url on the "
              "products/bundle download page. Can set multiple"),
    )
    parser.add_argument(
        '-b', '--write-buffer',
        type=str, default=1024*1024,
        help="Size of file buffer to use"
    )
    parser.add_argument(
        '--chunk_size','--chunk',
        type=str,
        help='Download Chunk Size'
    )
    parser.add_argument(
        '--timeout',
        type=str,
        help='Timeout (in seconds) for get requests'
    )    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in Debug Mode. Stops on Exceptions'
    )    
    parser.add_argument(
        '--keep',
        action='store_true',
        help='Keep files that fail download (ie: do not delete on failure)'
    )    
    

    return parser.parse_args(args)


def cli():
    cli_args = parse_args(sys.argv[1:])

    from .download_library import DownloadLibrary
    DownloadLibrary(
        cli_args.library_path,
        cookie_path=cli_args.cookie_file,
        cookie_auth=cli_args.session_auth,
        progress_bar=cli_args.progress,
        ext_include=cli_args.include,
        ext_exclude=cli_args.exclude,
        platform_include=cli_args.platform,
        purchase_keys=cli_args.keys,
        trove=cli_args.trove,
        update=cli_args.update,
        write_buffer=parse_size(cli_args.write_buffer),
        chunk_size=parse_size(cli_args.chunk_size),
        timeout=parse_seconds(cli_args.timeout),
        debug=cli_args.debug,
        keep=cli_args.keep,
    ).start()
