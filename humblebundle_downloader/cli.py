import os
import sys
import logging
import argparse

logger = logging.getLogger(__name__)

LOG_LEVEL = os.environ.get('HBD_LOGLEVEL', 'INFO').upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(message)s',
)
# Ignore unwanted logs from the requests lib when debuging
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)


def parse_args(args):
    if args[0].lower() == 'download':
        args = args[1:]
        raise DeprecationWarning("`download` argument is no longer used")

    parser = argparse.ArgumentParser()

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

    return parser.parse_args(args)


def cli():
    cli_args = parse_args(sys.argv[1:])

    from download_library import DownloadLibrary
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
    ).start()


if __name__ == "__main__":
    cli()