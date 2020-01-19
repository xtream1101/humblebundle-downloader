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
        default="hbd-cookies.txt",
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
        help="Location of the file to store the cookie",
        default="hbd-cookies.txt",
    )
    parser_download.add_argument(
        '-l', '--library-path', type=str,
        help="Folder to download all content to",
        required=True,
    )
    parser_download.add_argument(
        '--progress',
        action='store_true',
        help="Display progress bar for downloads",
    )

    cli_args = parser.parse_args()

    if cli_args.action == 'gen-cookies':
        from .generate_cookie import generate_cookie
        generate_cookie(cli_args.cookie_file)

    elif cli_args.action == 'download':
        from .download_library import download_library
        download_library(
            cli_args.cookie_file,
            cli_args.library_path,
            progress_bar=cli_args.progress
        )
