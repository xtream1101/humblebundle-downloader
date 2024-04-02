import os, csv
import multiprocessing
import logging
# internal import below.
from data.cache import CSV_CACHE, CsvCacheData, Cache
logger = logging.getLogger(__name__)

_HUMBLE_ENV_VAR = "HUMBLE_LIBRARY_PATH"
def rename_old_file(local_filepath, append_str):
    # Check if older file exists, if so rename
    if os.path.isfile(local_filepath) is True:
        filename_parts = local_filepath.rsplit('.', 1)
        new_name = "{name}_{append_str}.{ext}" \
            .format(name=filename_parts[0],
                    append_str=append_str,
                    ext=filename_parts[1])
        os.rename(local_filepath, new_name)
        logger.info("Renamed older file to {new_name}".format(new_name=new_name))


def download_file(product_r, local_filename, progress_bar=False) -> None:
    logger.info(f"Downloading: {os.path.basename(local_filename)} ")

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
                if progress_bar:
                    print("\t{percent}% [{filler}{space}]"  # this is nice.
                          .format(percent=int(done * (100 / pb_width)),
                                  filler='=' * done,
                                  space=' ' * (pb_width - done),
                                  ), end='\r')
            if dl != total_length:
                raise ValueError("Download did not complete")


def update_csv_cache(queue: multiprocessing.JoinableQueue):
    """
    use csv because json as on-disk data is wild.
    :param queue: the queue containing cache data
    """
    csv_filepath = os.path.join(get_library_path(), CSV_CACHE)
    with open(csv_filepath, 'a+') as outfile:
        while 1:
            try:
                cache_data: CsvCacheData = queue.get(True, 15.0)
            except:
                pass
            if "kill" == cache_data.key:
                queue.task_done()
                break

            csv.writer(outfile, delimiter=',', quotechar='"').writerow(cache_data)
            outfile.flush()
            queue.task_done()  # need 1 per queue.get


def load_cache_csv() -> Cache:
    try:
        csv_filepath = os.path.join(get_library_path(), CSV_CACHE)
        with open(csv_filepath, 'r') as cache_in:
            csv_stream = csv.reader(cache_in)
            cache_out = Cache([CsvCacheData(*row) for row in csv_stream])
    except FileNotFoundError:
        cache_out = Cache([])
    return cache_out


def create_product_folder(bundle_title: str, product_title: str) -> str:
    product_folder = os.path.join(get_library_path(), bundle_title, product_title)
    os.makedirs(product_folder, exist_ok=True)
    return product_folder


def set_library_path(library_path: str):
    os.environ[_HUMBLE_ENV_VAR] = library_path


def get_library_path():
    return os.environ[_HUMBLE_ENV_VAR]
