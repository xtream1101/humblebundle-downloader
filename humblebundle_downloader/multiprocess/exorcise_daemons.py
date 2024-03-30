"""
Author: Dakota Carter <slang.veteran-0s@icloud.com>
Description: Overwrite the multiprocess context to not create any daemons
"""
import multiprocessing.pool


class NoDaemonProcess(multiprocessing.Process):

    @property
    def daemon(self) -> bool:
        """
        We don't want any daemons so we return False here
        :return:
        """
        return False

    @daemon.setter
    def daemon(self, value: bool) -> None:
        """
        Just ignore the value trying to be set
        :param value: we literally do not care (but it would be a bool)
        """
        pass


class NoDaemonContext(type(multiprocessing.get_context())):
    Process = NoDaemonProcess


class ExorcistPool(multiprocessing.pool.Pool):
    """
    We subclass multiprocessing.pool.Pool instead of multiprocessing.Pool because the latter is only a wrapper
    not a proper class.
    """
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super(ExorcistPool, self).__init__(*args, **kwargs)