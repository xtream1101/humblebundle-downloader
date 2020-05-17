import os
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


def cli():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True

    ###
    # Download Library
    ###
    parser_download = subparsers.add_parser(
        'download',
        help="Download content in your humble bundle library",
    )
    parser_download.add_argument(
        '-c', '--cookie-file', type=str,
        help="Location of the cookies file",
        required=True,
    )
    parser_download.add_argument(
        '-l', '--library-path', type=str,
        help="Folder to download all content to",
        required=True,
    )
    parser_download.add_argument(
        '-t', '--trove', action='store_true',
        help="Only check and download Humble Trove content",
    )
    parser_download.add_argument(
        '-u', '--update', action='store_true',
        help=("Check to see if products have been updated "
              "(still get new products)"),
    )
    parser_download.add_argument(
        '-p', '--platform',
        type=str, nargs='*',
        help=("Only get content in a platform. Values can be seen in your "
              "humble bundle's library dropdown. Ex: -p ebook video"),
    )
    parser_download.add_argument(
        '--progress',
        action='store_true',
        help="Display progress bar for downloads",
    )
    filter_ext = parser_download.add_mutually_exclusive_group()
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
    parser_download.add_argument(
        '-k', '--keys',
        type=str, nargs='*',
        help=("The purchase download key. Find in the url on the "
              "products/bundle download page. Can set multiple"),
    )

    cli_args = parser.parse_args()

    if cli_args.action == 'download':
        # Still keep the download action to keep compatibility
        from .download_library import DownloadLibrary
        DownloadLibrary(
            cli_args.cookie_file,
            cli_args.library_path,
            progress_bar=cli_args.progress,
            ext_include=cli_args.include,
            ext_exclude=cli_args.exclude,
            platform_include=cli_args.platform,
            purchase_keys=cli_args.keys,
            trove=cli_args.trove,
            update=cli_args.update,
        ).start()
