

from dataclasses import dataclass
import logging

from fluf.plugin import fluf_hook_impl

lgr = logging.getLogger('__name__')


@dataclass
class FlufExecutorData:
    pass


class FlufExecutor():
    """ Function execution executor """

    @fluf_hook_impl
    def appinit(self, appdata):
        lgr.debug("Start")
        self.data = appdata.executor = FlufExecutorData()

    @fluf_hook_impl
    def get_priority(self, appdata, func):
        """ this executor shoud always work? """
        return 50, self

    @fluf_hook_impl
    def get_result(self, appdata, func, args, kwargs):
        lgr.debug("start execution")
        return func(*args, **kwargs)
        lgr.debug("finish execution")

    @fluf_hook_impl
    def appexit(self, appdata):
        lgr.debug("Exit")
