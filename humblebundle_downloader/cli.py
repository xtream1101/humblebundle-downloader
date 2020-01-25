import os
import logging
import argparse

logger = logging.getLogger(__name__)

LOG_LEVEL = os.environ.get('HBD_LOGLEVEL', 'INFO').upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(message)s',
)


def cli():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True

    ###
    # Generate cookie
    ###
    parser_gencookie = subparsers.add_parser(
        'gen-cookies',
        help="Generate cookies used to access your library",
    )
    parser_gencookie.add_argument(
        '-c', '--cookie-file', type=str,
        help="Location of the file to store the cookie",
        required=True,
    )

    ###
    # Download Library
    ###
    # TODO: have option to only get types, ebooks, videos, etc do not enforce,
    #       but lower and just string match to the type in the api
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

    if cli_args.action == 'gen-cookies':
        from .generate_cookie import generate_cookie
        generate_cookie(cli_args.cookie_file)

    elif cli_args.action == 'download':
        from .download_library import DownloadLibrary
        DownloadLibrary(
            cli_args.cookie_file,
            cli_args.library_path,
            progress_bar=cli_args.progress,
            ext_include=cli_args.include,
            ext_exclude=cli_args.exclude,
            platform_include=cli_args.platform,
            purchase_keys=cli_args.keys,
        ).start()
