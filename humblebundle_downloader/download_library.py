import os
import json
import parsel
import logging
import requests

logger = logging.getLogger(__name__)


def _clean_name(dirty_str):
    allowed_chars = (' ', '_', '.', '-', ':', '[', ']')
    return "".join([c for c in dirty_str.replace('+', '_') if c.isalpha() or c.isdigit() or c in allowed_chars]).strip()


def download_library(cookie_path, library_path, progress_bar=False):
    # Load cookies
    with open(cookie_path, 'r') as f:
        account_cookies = f.read()

    cache_file = os.path.join(library_path, '.cache.json')

    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
    except FileNotFoundError:
        cache_data = {}

    library_r = requests.get('https://www.humblebundle.com/home/library',
                             headers={'cookie': account_cookies})
    logger.debug(f"Library request: {library_r}")
    library_page = parsel.Selector(text=library_r.text)

    for order_id in json.loads(library_page.css('#user-home-json-data').xpath('string()').extract_first())['gamekeys']:
        order_r = requests.get(f'https://www.humblebundle.com/api/v1/order/{order_id}?all_tpkds=true',
                               headers={'cookie': account_cookies})
        logger.debug(f"Order request: {order_r}")
        order = order_r.json()
        bundle_title = _clean_name(order['product']['human_name'])
        logger.info(f"Checking bundle: {bundle_title}")
        for item in order['subproducts']:
            item_title = _clean_name(item['human_name'])
            # Get all types of download for a product
            for download_type in item['downloads']:
                # platform = download_type['platform']  # Type of product, ebook, videos, etc...
                item_folder = os.path.join(library_path, bundle_title, item_title)

                # Create directory to save the files to
                try: os.makedirs(item_folder)  # noqa: E701
                except OSError: pass  # noqa: E701

                # Download each file type of a product
                for file_type in download_type['download_struct']:
                    url = file_type['url']['web']
                    ext = url.split('?')[0].split('.')[-1]
                    filename = os.path.join(item_folder, f"{item_title}.{ext}")
                    item_r = requests.get(url, stream=True)
                    logger.debug(f"Item request: {item_r}, Url: {url}")
                    # Not sure which value will be best to use, so save them all for now
                    file_info = {
                        'md5': file_type['md5'],
                        'sha1': file_type['sha1'],
                        'url_last_modified': item_r.headers['Last-Modified'],
                        'url_etag': item_r.headers['ETag'][1:-1],
                        'url_crc': item_r.headers['X-HW-Cache-CRC'],
                    }
                    if file_info != cache_data.get(filename, {}):
                        if not progress_bar:
                            logger.info(f"Downloading: {item_title}.{ext}")

                        with open(filename, 'wb') as outfile:
                            total_length = item_r.headers.get('content-length')
                            if total_length is None:  # no content length header
                                outfile.write(item_r.content)
                            else:
                                dl = 0
                                total_length = int(total_length)
                                for data in item_r.iter_content(chunk_size=4096):
                                    dl += len(data)
                                    outfile.write(data)
                                    pb_width = 50
                                    done = int(pb_width * dl / total_length)
                                    if progress_bar: print(f"Downloading: {item_title}.{ext}: {int(done * (100 / pb_width))}% [{'=' * done}{' ' * (pb_width-done)}]", end='\r')  # noqa: E501, E701

                        if progress_bar:
                            print()  # print new line so next progress bar is on its own line

                        cache_data[filename] = file_info
                        # Update cache file with newest data so if the script quits it can keep track of the progress
                        with open(cache_file, 'w') as outfile:
                            json.dump(cache_data, outfile, sort_keys=True, indent=4)
