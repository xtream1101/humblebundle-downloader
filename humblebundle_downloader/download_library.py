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
    allowed_chars = (" ", "_", ".", "-", "[", "]")
    clean = []
    for c in dirty_str.replace("+", "_").replace(":", " -"):
        if c.isalpha() or c.isdigit() or c in allowed_chars:
            clean.append(c)

    return "".join(clean).strip().rstrip(".")


class DownloadLibrary:
    def __init__(
        self,
        library_path,
        cookie_path=None,
        cookie_auth=None,
        progress_bar=False,
        ext_include=None,
        ext_exclude=None,
        platform_include=None,
        purchase_keys=None,
        trove=False,
        update=False,
    ):
        self.library_path = library_path
        self.progress_bar = progress_bar
        self.ext_include = (
            [] if ext_include is None else list(map(str.lower, ext_include))
        )
        self.ext_exclude = (
            [] if ext_exclude is None else list(map(str.lower, ext_exclude))
        )

        if platform_include is None or "all" in platform_include:
            # if 'all', then do not need to use this check
            platform_include = []
        self.platform_include = list(map(str.lower, platform_include))

        self.purchase_keys = purchase_keys
        self.trove = trove
        self.update = update

        self.session = requests.Session()
        if cookie_path:
            try:
                cookie_jar = http.cookiejar.MozillaCookieJar(cookie_path)
                cookie_jar.load()
                self.session.cookies = cookie_jar
            except http.cookiejar.LoadError:
                # Still support the original cookie method
                with open(cookie_path, "r") as f:
                    self.session.headers.update({"cookie": f.read().strip()})
        elif cookie_auth:
            self.session.headers.update(
                {"cookie": "_simpleauth_sess={}".format(cookie_auth)}
            )

    def start(self):
        self.cache_file = os.path.join(self.library_path, ".cache.json")
        self.cache_data = self._load_cache_data(self.cache_file)
        self.purchase_keys = (
            self.purchase_keys if self.purchase_keys else self._get_purchase_keys()
        )

        if self.trove is True:
            logger.info("Only checking the Humble Trove...")
            for product in self._get_trove_products():
                title = _clean_name(product["human-name"])
                self._process_trove_product(title, product)
        else:
            for order_id in self.purchase_keys:
                self._process_order_id(order_id)

    def _get_trove_download_url(self, machine_name, web_name):
        try:
            sign_r = self.session.post(
                "https://www.humblebundle.com/api/v1/user/download/sign",
                data={
                    "machine_name": machine_name,
                    "filename": web_name,
                },
            )
        except Exception:
            logger.error(
                "Failed to get download url for trove product {title}".format(
                    title=web_name
                )
            )
            return None

        logger.debug("Signed url response {sign_r}".format(sign_r=sign_r))
        if sign_r.json().get("_errors") == "Unauthorized":
            logger.critical("Your account does not have access to the Trove")
            sys.exit()
        signed_url = sign_r.json()["signed_url"]
        logger.debug("Signed url {signed_url}".format(signed_url=signed_url))
        return signed_url

    def _process_trove_product(self, title, product):
        for platform, download in product["downloads"].items():
            # Sometimes the name has a dir in it
            # Example is "Broken Sword 5 - the Serpent's Curse"
            # Only the windows file has a dir like
            # "revolutionsoftware/BS5_v2.2.1-win32.zip"
            if self._should_download_platform(platform) is False:
                logger.info(
                    "Skipping {platform} for {product_title}".format(
                        platform=platform, product_title=title
                    )
                )
                continue

            web_name = download["url"]["web"].split("/")[-1]
            if self._should_download_file_by_ext_and_log(web_name) is False:
                continue

            cache_file_key = "trove:{name}".format(name=web_name)
            file_info = {
                "uploaded_at": (
                    download.get("uploaded_at")
                    or download.get("timestamp")
                    or product.get("date_added", "0")
                ),
                "md5": download.get("md5", "UNKNOWN_MD5"),
            }
            cache_file_info = self.cache_data.get(cache_file_key, {})

            if cache_file_info != {} and self.update is not True:
                # Do not care about checking for updates at this time
                continue

            if file_info["uploaded_at"] != cache_file_info.get(
                "uploaded_at"
            ) and file_info["md5"] != cache_file_info.get("md5"):
                product_folder = os.path.join(self.library_path, "Humble Trove", title)
                # Create directory to save the files to
                try:
                    os.makedirs(product_folder)
                except OSError:
                    pass
                local_filename = os.path.join(
                    product_folder,
                    web_name,
                )
                signed_url = self._get_trove_download_url(
                    download["machine_name"],
                    web_name,
                )
                if signed_url is None:
                    # Failed to get signed url. Error logged in fn
                    continue

                try:
                    product_r = self.session.get(signed_url, stream=True)
                except Exception:
                    logger.error(
                        "Failed to get trove product {title}".format(title=web_name)
                    )
                    continue

                if "uploaded_at" in cache_file_info:
                    uploaded_at = time.strftime(
                        "%Y-%m-%d", time.localtime(int(cache_file_info["uploaded_at"]))
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
        trove_base_url = "https://www.humblebundle.com/client/catalog?index={idx}"
        while True:
            logger.debug(
                "Collecting trove product data from api pg:{idx} ...".format(idx=idx)
            )
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
        order_url = "https://www.humblebundle.com/api/v1/order/{order_id}?all_tpkds=true".format(
            order_id=order_id
        )
        try:
            order_r = self.session.get(
                order_url,
                headers={
                    "content-type": "application/json",
                    "content-encoding": "gzip",
                },
            )
        except Exception:
            logger.error("Failed to get order key {order_id}".format(order_id=order_id))
            return

        logger.debug("Order request: {order_r}".format(order_r=order_r))
        order = order_r.json()
        bundle_title = _clean_name(order["product"]["human_name"])
        logger.info("Checking bundle: " + str(bundle_title))
        for product in order["subproducts"]:
            self._process_product(order_id, bundle_title, product)

    def _rename_old_file(self, local_filename, append_str):
        # Check if older file exists, if so rename
        if os.path.isfile(local_filename) is True:
            filename_parts = local_filename.rsplit(".", 1)
            new_name = "{name}_{append_str}.{ext}".format(
                name=filename_parts[0], append_str=append_str, ext=filename_parts[1]
            )
            os.rename(local_filename, new_name)
            logger.info("Renamed older file to {new_name}".format(new_name=new_name))

    def _process_product(self, order_id, bundle_title, product):
        product_title = _clean_name(product["human_name"])
        # Get all types of download for a product
        for download_type in product["downloads"]:
            if self._should_download_platform(download_type["platform"]) is False:
                logger.info(
                    "Skipping {platform} for {product_title}".format(
                        platform=download_type["platform"], product_title=product_title
                    )
                )
                continue

            product_folder = os.path.join(
                self.library_path, bundle_title, product_title
            )
            # Create directory to save the files to
            try:
                os.makedirs(product_folder)
            except OSError:
                pass

            # Download each file type of a product
            for file_type in download_type["download_struct"]:
                try:
                    if "url" in file_type and "web" in file_type["url"]:
                        # downloadable URL
                        url = file_type["url"]["web"]

                        url_filename = url.split("?")[0].split("/")[-1]

                        if (
                            self._should_download_file_by_ext_and_log(url_filename)
                            is False
                        ):
                            continue

                        cache_file_key = order_id + ":" + url_filename
                        try:
                            self._check_cache_and_download(
                                cache_file_key, url, product_folder, url_filename
                            )
                        except FileExistsError:
                            continue
                        except Exception:
                            logger.exception("Failed to download {url}".format(url=url))
                    elif "asm_config" in file_type:
                        # asm.js game playable directly in the browser
                        game_name = file_type["asm_config"]["display_item"]
                        local_folder = os.path.join(product_folder, game_name)
                        # Create directory to save the files to
                        try:
                            os.makedirs(local_folder, exist_ok=True)  # noqa: E701
                        except OSError:
                            pass  # noqa: E701

                        # get the HTML file that presents the game, used in the Humble web interface iframe
                        asmjs_html_filename = game_name + ".html"
                        asmjs_local_html_filename = game_name + ".local.html"
                        cache_file_key = order_id + ":" + asmjs_html_filename
                        # game_name might be "game" or "game_asm" but the path to the file here always uses the "game_asm" version
                        game_asm_name = file_type["asm_manifest"]["asmFile"].split("/")[
                            2
                        ]
                        asmjs_url = (
                            "https://www.humblebundle.com/play/asmjs/"
                            + game_asm_name
                            + "/"
                            + order_id
                        )

                        if (
                            self._should_download_file_by_ext_and_log(
                                asmjs_html_filename
                            )
                            is False
                        ):
                            continue

                        downloaded = False
                        try:
                            downloaded = self._check_cache_and_download(
                                cache_file_key,
                                asmjs_url,
                                local_folder,
                                asmjs_html_filename,
                            )
                        except FileExistsError:
                            pass  # we should download the asm/data files even if the html file was previously downloaded
                        except Exception:
                            logger.exception(
                                "Failed to download {asmjs_url}".format(
                                    asmjs_url=asmjs_url
                                )
                            )
                            continue

                        # read from the html file a version of file_type['asm_manifest'] with HMAC/etc auth params on the URLs
                        with open(
                            os.path.join(local_folder, asmjs_html_filename), "r"
                        ) as asmjs_html:
                            asmjs_page = parsel.Selector(text=asmjs_html.read())
                            asm_player_data_text = asmjs_page.css(
                                "#webpack-asm-player-data::text"
                            ).get()  # noqa: E501
                            asm_player_data = json.loads(asm_player_data_text)

                        if downloaded:
                            # create the local playable version of the html file
                            # by replacing remote manifest URLs with the local filename
                            try:
                                with open(
                                    os.path.join(local_folder, asmjs_html_filename), "r"
                                ) as asmjs_html:
                                    with open(
                                        os.path.join(
                                            local_folder, asmjs_local_html_filename
                                        ),
                                        "w",
                                    ) as asmjs_local_html:
                                        for line in asmjs_html:
                                            for (
                                                local_filename,
                                                remote_file,
                                            ) in asm_player_data["asmOptions"][
                                                "manifest"
                                            ].items():
                                                line = line.replace(
                                                    f'"{local_filename}": "{remote_file}"',
                                                    f'"{local_filename}": "{local_filename}"',
                                                )
                                            asmjs_local_html.write(line)
                            except Exception:
                                logger.exception(
                                    "Failed to create local version of {asmjs_html_filename}".format(
                                        asmjs_html_filename=asmjs_html_filename
                                    )
                                )

                        # TODO deduplicate these files? Osmos example has 3 unique files and 2 dupes with different names
                        for local_filename, remote_file in asm_player_data[
                            "asmOptions"
                        ]["manifest"].items():
                            cache_file_key = (
                                order_id + ":" + game_name + ":" + local_filename
                            )
                            try:
                                self._check_cache_and_download(
                                    cache_file_key,
                                    remote_file,
                                    local_folder,
                                    local_filename,
                                )
                            except FileExistsError:
                                continue
                            except Exception:
                                logger.exception(
                                    "Failed to download {url}".format(url=url)
                                )
                                continue

                    elif "external_link" in file_type:
                        logger.info(
                            "External url found: {bundle_title}/{product_title} : {url}".format(
                                bundle_title=bundle_title,
                                product_title=product_title,
                                url=file_type["external_link"],
                            )
                        )

                    else:
                        logger.info(
                            "No downloadable url(s) found: {bundle_title}/{product_title}".format(
                                bundle_title=bundle_title, product_title=product_title
                            )
                        )
                        logger.info(file_type)
                        continue
                except Exception:
                    logger.exception(
                        "Failed to download this 'file':\n{file_type}".format(
                            file_type=file_type
                        )
                    )
                    continue

    def _update_cache_data(self, cache_file_key, file_info):
        self.cache_data[cache_file_key] = file_info
        # Update cache file with newest data so if the script
        # quits it can keep track of the progress
        # Note: Only safe because of single thread,
        # need to change if refactor to multi threading
        with open(self.cache_file, "w") as outfile:
            json.dump(
                self.cache_data,
                outfile,
                sort_keys=True,
                indent=4,
            )

    def _check_cache_and_download(
        self, cache_file_key, remote_file, local_folder, local_filename
    ):
        cache_file_info = self.cache_data.get(cache_file_key, {})

        if cache_file_info != {} and self.update is not True:
            # Do not care about checking for updates at this time
            raise FileExistsError

        try:
            remote_file_r = self.session.get(remote_file, stream=True)
        except Exception:
            logger.exception(
                "Failed to download {remote_file}".format(remote_file=remote_file)
            )
            return False

        # Check to see if the file still exists
        if remote_file_r.status_code != 200:
            logger.debug(
                "File unavailable {remote_file} status code {status_code}".format(
                    remote_file=remote_file, status_code=remote_file_r.status_code
                )
            )
            return False

        logger.debug(
            "Item request: {remote_file_r}, Url: {remote_file}".format(
                remote_file_r=remote_file_r, remote_file=remote_file
            )
        )
        file_info = {}
        if "Last-Modified" in remote_file_r.headers:
            file_info["url_last_modified"] = remote_file_r.headers["Last-Modified"]
            if file_info["url_last_modified"] == cache_file_info.get(
                "url_last_modified"
            ):
                return False
        if "url_last_modified" in cache_file_info:
            last_modified = datetime.datetime.strptime(
                cache_file_info["url_last_modified"], "%a, %d %b %Y %H:%M:%S %Z"
            ).strftime("%Y-%m-%d")
        else:
            last_modified = None

        local_file = os.path.join(local_folder, local_filename)
        # Create directory to save the file to, which might not exist if there's a subdirectory included
        try:
            os.makedirs(os.path.dirname(local_file), exist_ok=True)  # noqa: E701
        except OSError:
            raise  # noqa: E701

        return self._process_download(
            remote_file_r,
            cache_file_key,
            file_info,
            local_file,
            rename_str=last_modified,
        )

    def _process_download(
        self, open_r, cache_file_key, file_info, local_filename, rename_str=None
    ):
        try:
            if rename_str:
                self._rename_old_file(local_filename, rename_str)

            self._download_file(open_r, local_filename)

        except (Exception, KeyboardInterrupt) as e:
            if self.progress_bar:
                # Do not overwrite the progress bar on next print
                print()
            logger.error(
                "Failed to download file {local_filename}".format(
                    local_filename=local_filename
                )
            )

            # Clean up broken downloaded file
            try:
                os.remove(local_filename)
            except OSError:
                pass

            if type(e).__name__ == "KeyboardInterrupt":
                sys.exit()

            return False

        else:
            if self.progress_bar:
                # Do not overwrite the progress bar on next print
                print()
            if "url_last_modified" not in file_info:
                # no Last-Modified header so we set the time of the current download
                # this will result in the file not being re-downloaded by default later
                file_info["url_last_modified"] = datetime.datetime.now().strftime(
                    "%a, %d %b %Y %H:%M:%S %Z"
                )
            self._update_cache_data(cache_file_key, file_info)

        finally:
            # Since its a stream connection, make sure to close it
            open_r.connection.close()
            return True

    def _download_file(self, product_r, local_filename):
        logger.info(
            "Downloading: {local_filename}".format(local_filename=local_filename)
        )

        with open(local_filename, "wb") as outfile:
            total_length = product_r.headers.get("content-length")
            if total_length is None:  # no content length header
                dl = 0
                for data in product_r.iter_content(chunk_size=4096):
                    dl += len(data)
                    outfile.write(data)
                    if self.progress_bar:
                        print(
                            "\t{dl}".format(dl=dl),
                            end="\r",
                        )
            else:
                dl = 0
                total_length = int(total_length)
                for data in product_r.iter_content(chunk_size=4096):
                    dl += len(data)
                    outfile.write(data)
                    pb_width = 50
                    done = int(pb_width * dl / total_length)
                    if self.progress_bar:
                        print(
                            "\t{percent}% [{filler}{space}]".format(
                                percent=int(done * (100 / pb_width)),
                                filler="=" * min(max(done, 0), pb_width),
                                space=" " * min(max((pb_width - done), 0), pb_width),
                            ),
                            end="\r",
                        )

                if dl < total_length:
                    raise ValueError("Download did not complete")
                if dl > total_length:
                    print()
                    logger.warn("Downloaded more content than expected")

    def _load_cache_data(self, cache_file):
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
        except FileNotFoundError:
            cache_data = {}

        return cache_data

    def _get_purchase_keys(self):
        try:
            library_r = self.session.get("https://www.humblebundle.com/home/library")
        except Exception:
            logger.exception("Failed to get list of purchases")
            return []

        logger.debug("Library request: " + str(library_r))
        library_page = parsel.Selector(text=library_r.text)
        user_data = (
            library_page.css("#user-home-json-data").xpath("string()").extract_first()
        )
        if user_data is None:
            raise Exception("Unable to download user-data, cookies missing?")
        orders_json = json.loads(user_data)
        return orders_json["gamekeys"]

    def _should_download_platform(self, platform):
        platform = platform.lower()
        if self.platform_include and platform not in self.platform_include:
            return False
        return True

    def _should_download_file_by_ext_and_log(self, filename):
        if self._should_download_file_by_ext(filename) is False:
            logger.info("Skipping the file {filename}".format(filename=filename))
            return False
        return True

    def _should_download_file_by_ext(self, filename):
        ext = filename.split(".")[-1]
        return self._should_download_ext(ext)

    def _should_download_ext(self, ext):
        ext = ext.lower()
        if self.ext_include != []:
            return ext in self.ext_include
        elif self.ext_exclude != []:
            return ext not in self.ext_exclude
        return True
