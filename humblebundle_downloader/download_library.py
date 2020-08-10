import os
import sys
import json
import time
import parsel
import logging
import datetime
import requests
import http.cookiejar

logger = logging.getLogger(__name__)


def _clean_name(dirty_str):
    allowed_chars = (' ', '_', '.', '-', '[', ']')
    clean = []
    for c in dirty_str.replace('+', '_').replace(':', ' -'):
        if c.isalpha() or c.isdigit() or c in allowed_chars:
            clean.append(c)

    return "".join(clean).strip().rstrip('.')


class DownloadLibrary:

    def __init__(self, cookie_path, library_path, progress_bar=False,
                 ext_include=None, ext_exclude=None, platform_include=None,
                 purchase_keys=None, trove=False, update=False):
        self.library_path = library_path
        self.progress_bar = progress_bar
        self.ext_include = [] if ext_include is None else list(map(str.lower, ext_include))  # noqa: E501
        self.ext_exclude = [] if ext_exclude is None else list(map(str.lower, ext_exclude))  # noqa: E501

        if platform_include is None or 'all' in platform_include:
            # if 'all', then do not need to use this check
            platform_include = []
        self.platform_include = list(map(str.lower, platform_include))

        self.cache_file = os.path.join(library_path, '.cache.json')
        self.purchase_keys = purchase_keys
        self.trove = trove
        self.update = update

        self.session = requests.Session()
        try:
            cookie_jar = http.cookiejar.MozillaCookieJar(cookie_path)
            cookie_jar.load()
            self.session.cookies = cookie_jar
        except http.cookiejar.LoadError:
            # Still support the original cookie method
            with open(cookie_path, 'r') as f:
                self.session.headers.update({'cookie': f.read().strip()})

    def start(self):

        self.cache_data = self._load_cache_data(self.cache_file)
        self.purchase_keys = self.purchase_keys if self.purchase_keys else self._get_purchase_keys()  # noqa: E501

        if self.trove is True:
            logger.info("Only checking the Humble Trove...")
            for product in self._get_trove_products():
                title = _clean_name(product['human-name'])
                self._process_trove_product(title, product)
        else:
            for order_id in self.purchase_keys:
                self._process_order_id(order_id)

    def _get_trove_download_url(self, machine_name, web_name):
        try:
            sign_r = self.session.post(
                'https://www.humblebundle.com/api/v1/user/download/sign',
                data={
                    'machine_name': machine_name,
                    'filename': web_name,
                },
            )
        except Exception:
            logger.error("Failed to get download url for trove product {title}"
                         .format(title=web_name))
            return None

        logger.debug("Signed url response {sign_r}".format(sign_r=sign_r))
        if sign_r.json().get('_errors') == 'Unauthorized':
            logger.critical("Your account does not have access to the Trove")
            sys.exit()
        signed_url = sign_r.json()['signed_url']
        logger.debug("Signed url {signed_url}".format(signed_url=signed_url))
        return signed_url

    def _process_trove_product(self, title, product):
        for platform, download in product['downloads'].items():
            # Sometimes the name has a dir in it
            # Example is "Broken Sword 5 - the Serpent's Curse"
            # Only the windows file has a dir like
            # "revolutionsoftware/BS5_v2.2.1-win32.zip"
            if self._should_download_platform(platform) is False:  # noqa: E501
                logger.info("Skipping {platform} for {product_title}"
                            .format(platform=platform,
                                    product_title=title))
                continue

            web_name = download['url']['web'].split('/')[-1]
            ext = web_name.split('.')[-1]
            if self._should_download_file_type(ext) is False:
                logger.info("Skipping the file {web_name}"
                            .format(web_name=web_name))
                continue

            cache_file_key = 'trove:{name}'.format(name=web_name)
            file_info = {
                'uploaded_at': download.get('uploaded_at'),
                'md5': download.get('md5'),
            }
            cache_file_info = self.cache_data.get(cache_file_key, {})

            if cache_file_info != {} and self.update is not True:
                # Do not care about checking for updates at this time
                continue

            if (file_info['uploaded_at'] != cache_file_info.get('uploaded_at')
                    and file_info['md5'] != cache_file_info.get('md5')):
                product_folder = os.path.join(
                    self.library_path, 'Humble Trove', title
                )
                # Create directory to save the files to
                try: os.makedirs(product_folder)  # noqa: E701
                except OSError: pass  # noqa: E701
                local_filename = os.path.join(
                    product_folder,
                    web_name,
                )
                signed_url = self._get_trove_download_url(
                    download['machine_name'],
                    web_name,
                )
                if signed_url is None:
                    # Failed to get signed url. Error logged in fn
                    continue

                try:
                    product_r = self.session.get(signed_url, stream=True)
                except Exception:
                    logger.error("Failed to get trove product {title}"
                                 .format(title=web_name))
                    continue

                if 'uploaded_at' in cache_file_info:
                    uploaded_at = time.strftime(
                        '%Y-%m-%d',
                        time.localtime(int(cache_file_info['uploaded_at']))
                    )
                else:
                    uploaded_at = None

                self._process_download(
                    product_r,
                    cache_file_key,
                    file_info,
                    local_filename,
                    rename_str=uploaded_at,
                )

    def _get_trove_products(self):
        trove_products = []
        idx = 0
        trove_base_url = 'https://www.humblebundle.com/api/v1/trove/chunk?property=popularity&direction=desc&index={idx}'   # noqa: E501
        while True:
            logger.debug("Collecting trove product data from api pg:{idx} ..."
                         .format(idx=idx))
            trove_page_url = trove_base_url.format(idx=idx)
            try:
                trove_r = self.session.get(trove_page_url)
            except Exception:
                logger.error("Failed to get products from Humble Trove")
                return []

            page_content = trove_r.json()

            if len(page_content) == 0:
                break

            trove_products.extend(page_content)
            idx += 1

        return trove_products

    def _process_order_id(self, order_id):
        order_url = 'https://www.humblebundle.com/api/v1/order/{order_id}?all_tpkds=true'.format(order_id=order_id)  # noqa: E501
        try:
            order_r = self.session.get(
                order_url,
                headers={
                    'content-type': 'application/json',
                    'content-encoding': 'gzip',
                },
            )
        except Exception:
            logger.error("Failed to get order key {order_id}"
                         .format(order_id=order_id))
            return

        logger.debug("Order request: {order_r}".format(order_r=order_r))
        order = order_r.json()
        bundle_title = _clean_name(order['product']['human_name'])
        logger.info("Checking bundle: " + str(bundle_title))
        for product in order['subproducts']:
            self._process_product(order_id, bundle_title, product)

    def _rename_old_file(self, local_filename, append_str):
        # Check if older file exists, if so rename
        if os.path.isfile(local_filename) is True:
            filename_parts = local_filename.rsplit('.', 1)
            new_name = "{name}_{append_str}.{ext}"\
                       .format(name=filename_parts[0],
                               append_str=append_str,
                               ext=filename_parts[1])
            os.rename(local_filename, new_name)
            logger.info("Renamed older file to {new_name}"
                        .format(new_name=new_name))

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
                cache_file_info = self.cache_data.get(cache_file_key, {})

                if cache_file_info != {} and self.update is not True:
                    # Do not care about checking for updates at this time
                    continue

                try:
                    product_r = self.session.get(url, stream=True)
                except Exception:
                    logger.error("Failed to download {url}".format(url=url))
                    continue

                logger.debug("Item request: {product_r}, Url: {url}"
                             .format(product_r=product_r, url=url))
                file_info = {
                    'url_last_modified': product_r.headers['Last-Modified'],
                }
                if file_info['url_last_modified'] != cache_file_info.get('url_last_modified'):  # noqa: E501
                    if 'url_last_modified' in cache_file_info:
                        last_modified = datetime.datetime.strptime(
                            cache_file_info['url_last_modified'],
                            '%a, %d %b %Y %H:%M:%S %Z'
                        ).strftime('%Y-%m-%d')
                    else:
                        last_modified = None
                    self._process_download(
                        product_r,
                        cache_file_key,
                        file_info,
                        local_filename,
                        rename_str=last_modified,
                    )

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

    def _process_download(self, open_r, cache_file_key, file_info,
                          local_filename, rename_str=None):
        try:
            if rename_str:
                self._rename_old_file(local_filename, rename_str)

            self._download_file(open_r, local_filename)

        except (Exception, KeyboardInterrupt) as e:
            if self.progress_bar:
                # Do not overwrite the progress bar on next print
                print()
            logger.error("Failed to download file {local_filename}"
                         .format(local_filename=local_filename))

            # Clean up broken downloaded file
            try: os.remove(local_filename)  # noqa: E701
            except OSError: pass  # noqa: E701

            if type(e).__name__ == 'KeyboardInterrupt':
                sys.exit()

        else:
            if self.progress_bar:
                # Do not overwrite the progress bar on next print
                print()
            self._update_cache_data(cache_file_key, file_info)

        finally:
            # Since its a stream connection, make sure to close it
            open_r.connection.close()

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
                              .format(percent=int(done * (100 / pb_width)),
                                      filler='=' * done,
                                      space=' ' * (pb_width - done),
                                      ), end='\r')

                if dl != total_length:
                    raise ValueError("Download did not complete")

    def _load_cache_data(self, cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
        except FileNotFoundError:
            cache_data = {}

        return cache_data

    def _get_purchase_keys(self):
        try:
            library_r = self.session.get('https://www.humblebundle.com/home/library')  # noqa: E501
        except Exception:
            logger.exception("Failed to get list of purchases")
            return []

        logger.debug("Library request: " + str(library_r))
        library_page = parsel.Selector(text=library_r.text)
        user_data = library_page.css('#user-home-json-data').xpath('string()').extract_first()  # noqa: E501
        if user_data is None:
            raise Exception("Unable to download user-data, cookies missing?")
        orders_json = json.loads(user_data)
        return orders_json['gamekeys']

    def _should_download_platform(self, platform):
        platform = platform.lower()
        if self.platform_include and platform not in self.platform_include:
            return False
        return True

    def _should_download_file_type(self, ext):
        ext = ext.lower()
        if self.ext_include != []:
            return ext in self.ext_include
        elif self.ext_exclude != []:
            return ext not in self.ext_exclude
        return True
