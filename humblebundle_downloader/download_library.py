import os
import sys
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


class DownloadLibrary:

    def __init__(self, cookie_path, library_path, progress_bar=False,
                 ext_include=None, ext_exclude=None, platform_include=None,
                 purchase_keys=None):

        with open(cookie_path, 'r') as f:
            self.account_cookies = f.read()

        self.library_path = library_path
        self.progress_bar = progress_bar
        self.ext_include = [] if ext_include is None else list(map(str.lower, ext_include))  # noqa: E501
        self.ext_exclude = [] if ext_exclude is None else list(map(str.lower, ext_exclude))  # noqa: E501

        if platform_include is None or 'all' in platform_include:
            # if 'all', then do not need to use this check
            platform_include = []
        self.platform_include = list(map(str.lower, platform_include))

        self.cache_file = os.path.join(library_path, '.cache.json')
        self.cache_data = self._load_cache_data(self.cache_file)

        self.purchase_keys = purchase_keys if purchase_keys else self._get_purchase_keys()  # noqa: E501

    def start(self):
        for order_id in self.purchase_keys:
            self._process_order_id(order_id)

    def _process_order_id(self, order_id):
        order_url = 'https://www.humblebundle.com/api/v1/order/{order_id}?all_tpkds=true'.format(order_id=order_id)  # noqa: E501
        order_r = requests.get(order_url,
                               headers={'cookie': self.account_cookies})
        logger.debug("Order request: {order_r}".format(order_r=order_r))
        order = order_r.json()
        bundle_title = _clean_name(order['product']['human_name'])
        logger.info("Checking bundle: " + str(bundle_title))
        for product in order['subproducts']:
            self._process_product(order_id, bundle_title, product)

    def _process_product(self, order_id, bundle_title, product):
        product_title = _clean_name(product['human_name'])
        # Get all types of download for a product
        for download_type in product['downloads']:
            if self._should_download_platform(download_type['platform']) is False:  # noqa: E501
                logger.info("Skipping {platform} for {product_title}"
                            .format(platform=download_type['platform'],
                                    product_title=product_title))
                continue

            product_folder = os.path.join(
                self.library_path, bundle_title, product_title
            )

            # Create directory to save the files to
            try: os.makedirs(product_folder)  # noqa: E701
            except OSError: pass  # noqa: E701

            # Download each file type of a product
            for file_type in download_type['download_struct']:
                try:
                    url = file_type['url']['web']
                except KeyError:
                    logger.info("No url found: {bundle_title}/{product_title}"
                                .format(bundle_title=bundle_title,
                                        product_title=product_title))
                    continue

                url_filename = url.split('?')[0].split('/')[-1]
                cache_file_key = order_id + ':' + url_filename
                ext = url_filename.split('.')[-1]
                if self._should_download_file_type(ext) is False:
                    logger.info("Skipping the file {url_filename}"
                                .format(url_filename=url_filename))
                    continue

                local_filename = os.path.join(product_folder, url_filename)
                product_r = requests.get(url, stream=True)
                logger.debug("Item request: {product_r}, Url: {url}"
                             .format(product_r=product_r, url=url))
                # Not sure which value will be best to use, so use them all
                file_info = {
                    'md5': file_type.get('md5'),
                    'sha1': file_type.get('sha1'),
                    'url_last_modified': product_r.headers['Last-Modified'],
                    'url_etag': product_r.headers['ETag'][1:-1],
                    'url_crc': product_r.headers['X-HW-Cache-CRC'],
                }
                if file_info != self.cache_data.get(cache_file_key, {}):
                    try:
                        self._download_file(product_r, local_filename)

                    except (Exception, KeyboardInterrupt) as e:
                        if self.progress_bar:
                            # Do not overwrite the progress bar on next print
                            print()
                        logger.error("Failed to download file {product_title}/{url_filename}"  # noqa: E501
                                     .format(product_title=product_title,
                                             url_filename=url_filename))

                        # Clean up broken downloaded file
                        try: os.remove(local_filename)  # noqa: E701
                        except OSError: pass  # noqa: E701

                        if type(e).__name__ == 'KeyboardInterrupt':
                            sys.exit()
                        else:
                            continue

                    else:
                        if self.progress_bar:
                            # Do not overwrite the progress bar on next print
                            print()
                        self._update_cache_data(cache_file_key, file_info)

                    finally:
                        # Since its a stream connection, make sure to close it
                        product_r.connection.close()

    def _update_cache_data(self, cache_file_key, file_info):
        self.cache_data[cache_file_key] = file_info
        # Update cache file with newest data so if the script
        # quits it can keep track of the progress
        # Note: Only safe because of single thread,
        # need to change if refactor to multi threading
        with open(self.cache_file, 'w') as outfile:
            json.dump(
                self.cache_data, outfile,
                sort_keys=True, indent=4,
            )

    def _download_file(self, product_r, local_filename):
        logger.info("Downloading: {local_filename}"
                    .format(local_filename=local_filename))

        with open(local_filename, 'wb') as outfile:
            total_length = product_r.headers.get('content-length')
            if total_length is None:  # no content length header
                outfile.write(product_r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in product_r.iter_content(chunk_size=4096):
                    dl += len(data)
                    outfile.write(data)
                    pb_width = 50
                    done = int(pb_width * dl / total_length)
                    if self.progress_bar:
                        print("\t{percent}% [{filler}{space}]"
                              .format(local_filename=local_filename,
                                      percent=int(done * (100 / pb_width)),
                                      filler='=' * done,
                                      space=' ' * (pb_width - done),
                                      ), end='\r')

    def _load_cache_data(self, cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
        except FileNotFoundError:
            cache_data = {}

        return cache_data

    def _get_purchase_keys(self):
        library_r = requests.get('https://www.humblebundle.com/home/library',
                                 headers={'cookie': self.account_cookies})
        logger.debug("Library request: " + str(library_r))
        library_page = parsel.Selector(text=library_r.text)
        orders_json = json.loads(library_page.css('#user-home-json-data')
                                             .xpath('string()').extract_first())
        return orders_json['gamekeys']

    def _should_download_platform(self, platform):
        platform = platform.lower()
        return self.platform_include and platform not in self.platform_include

    def _should_download_file_type(self, ext):
        ext = ext.lower()
        return ((self.ext_include and ext.lower() not in self.ext_include)
                or (self.ext_exclude and ext.lower() in self.ext_exclude))
