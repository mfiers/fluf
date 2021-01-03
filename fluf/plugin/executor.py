

import logging

from fluf.plugin import fluf_hook_impl

lgr = logging.getLogger('__name__')
lgr.setLevel(logging.WARNING)


class FlufExecutor():
    """ Function execution executor """

    @fluf_hook_impl
    def get_priority(self, app, func, fcall, finvoc):
        """ this executor shoud always work? """
        return 50, self

    @fluf_hook_impl
    def get_result(self, app, func, fcall, finvoc, args, kwargs):
        lgr.debug("start execution")
        try:
            rv = func(*args, **kwargs)
            finvoc.success = True
            finvoc.from_cache = False
            return rv
        except:
            lgr.warning(f"Failed running function {fcall}")
            finvoc.success = False
            fcall.dirty = True
            finvoc.save()
            fcall.save()
            raise
