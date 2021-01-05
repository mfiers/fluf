
import logging

from fluf.plugin import fluf_hook_impl

lgr = logging.getLogger(__name__)
lgr.setLevel(logging.INFO)


class FlufMemcache():
    """ Function execution memcache """

    @fluf_hook_impl
    def app_init(self, app):
        lgr.debug("Initialze memcache")
        self.data = {}


    @fluf_hook_impl
    def get_priority(self, app, func, fcall, finvoc):
        """ only run when in memcache - but then with high priority """
        if fcall.uid in self.data:
            # we have this call cached -
            return 10, self
        else:
            # we do not have the call (yet)
            return 1000, self

    @fluf_hook_impl
    def get_result(self, app, func, fcall, finvoc, args, kwargs):
        lgr.debug(f"Return call {fcall} from memcache")
        try:
            rv = self.data[fcall.uid]
            finvoc.success = True
            finvoc.from_cache = True
            return rv
        except:
            finvoc.success = False
            finvoc.save()
            fcall.save()

    @fluf_hook_impl
    def on_success_call(self, app, func, fcall, finvoc, rv):
        lgr.debug(f"store call {fcall} in memcache")
        self.data[fcall.uid] = rv
