import os
import json
import parsel
import logging
import requests

logger = logging.getLogger(__name__)


def _clean_name(dirty_str):
    allowed_chars = (' ', '_', '.', '-', '[', ']')
    clean = []
    for c in dirty_str.replace('+', '_').replace(':', ' -'):
        if c.isalpha() or c.isdigit() or c in allowed_chars:
            clean.append(c)

    return "".join(clean).strip()


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
    logger.debug("Library request: " + str(library_r))
    library_page = parsel.Selector(text=library_r.text)
    orders_json = json.loads(library_page.css('#user-home-json-data')
                                         .xpath('string()').extract_first())

    for order_id in orders_json['gamekeys']:
        order_url = 'https://www.humblebundle.com/api/v1/order/{order_id}?all_tpkds=true'.format(order_id=order_id)  # noqa: E501
        order_r = requests.get(order_url,
                               headers={'cookie': account_cookies})
        logger.debug("Order request: " + str(order_r))
        order = order_r.json()
        bundle_title = _clean_name(order['product']['human_name'])
        logger.info("Checking bundle: " + str(bundle_title))
        for item in order['subproducts']:
            item_title = _clean_name(item['human_name'])
            # Get all types of download for a product
            for download_type in item['downloads']:
                # Type of product, ebook, videos, etc...
                # platform = download_type['platform']
                item_folder = os.path.join(
                    library_path, bundle_title, item_title
                )

                # Create directory to save the files to
                try: os.makedirs(item_folder)  # noqa: E701
                except OSError: pass  # noqa: E701

                # Download each file type of a product
                for file_type in download_type['download_struct']:
                    try:
                        url = file_type['url']['web']
                    except KeyError:
                        logger.info("No url found for " + item_title)
                        continue
                    ext = url.split('?')[0].split('.')[-1]
                    file_title = item_title + "." + ext
                    filename = os.path.join(item_folder, file_title)
                    item_r = requests.get(url, stream=True)
                    logger.debug("Item request: {item_r}, Url: {url}"
                                 .format(item_r=item_r, url=url))
                    # Not sure which value will be best to use, so use them all
                    file_info = {
                        'md5': file_type.get('md5'),
                        'sha1': file_type.get('sha1'),
                        'url_last_modified': item_r.headers['Last-Modified'],
                        'url_etag': item_r.headers['ETag'][1:-1],
                        'url_crc': item_r.headers['X-HW-Cache-CRC'],
                    }
                    if file_info != cache_data.get(filename, {}):
                        if not progress_bar:
                            logger.info("Downloading: {file_title}"
                                        .format(file_title=file_title))

                        with open(filename, 'wb') as outfile:
                            total_length = item_r.headers.get('content-length')
                            if total_length is None:  # no content length header
                                outfile.write(item_r.content)
                            else:
                                dl = 0
                                total_length = int(total_length)
                                for data in item_r.iter_content(chunk_size=4096):  # noqa E501
                                    dl += len(data)
                                    outfile.write(data)
                                    pb_width = 50
                                    done = int(pb_width * dl / total_length)
                                    if progress_bar:
                                        print("Downloading: {file_title}: {percent}% [{filler}{space}]"  # noqa E501
                                              .format(file_title=file_title,
                                                      percent=int(done * (100 / pb_width)),  # noqa E501
                                                      filler='=' * done,
                                                       space=' ' * (pb_width - done),  # noqa E501
                                                      ), end='\r')

                        if progress_bar:
                            # print new line so next progress bar
                            # is on its own line
                            print()

                        cache_data[filename] = file_info
                        # Update cache file with newest data so if the script
                        # quits it can keep track of the progress
                        with open(cache_file, 'w') as outfile:
                            json.dump(
                                cache_data, outfile,
                                sort_keys=True, indent=4,
                            )
