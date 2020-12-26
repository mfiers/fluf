

from dataclasses import dataclass
import logging

from fluf.plugin import fluf_hook_impl

lgr = logging.getLogger('__name__')


@dataclass
class FlufMemcacheData:
    pass


class FlufMemcache():
    """ Function execution memcache """

    @fluf_hook_impl
    def appinit(self, appdata):
        lgr.debug("Start")
        self.data = appdata.memcache = FlufMemcacheData()

    @fluf_hook_impl
    def get_priority(self, appdata, func):
        """ only run when in memcache - but then with high priority """
        return 49, self

    @fluf_hook_impl
    def get_result(self, appdata, func, args, kwargs):
        lgr.debug("start execution")
        return 'memcache (NOT YET)'
        lgr.debug("finish execution")

    @fluf_hook_impl
    def appexit(self, appdata):
        lgr.debug("Exit")
