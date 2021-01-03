

from datetime import datetime
import logging
import os
import socket

from fluf.plugin import fluf_hook_impl

lgr = logging.getLogger('__name__')


class FlufLogger():
    """ Function execution logger """

    @fluf_hook_impl
    def app_init(self, app):
        lgr.debug("Start")
        self.appstart = datetime.now()

    @fluf_hook_impl
    def prepare_call(self, app, func, fcall, finvoc, args, kwargs):
        finvoc.start = datetime.now()
        finvoc.addkeyval('hostname', socket.gethostname())
        finvoc.addkeyval('pwd', os.getcwd())

    @fluf_hook_impl(trylast=True)
    def finish_call(self, app, func, fcall, finvoc, rv):
        finvoc.end = datetime.now()

    @fluf_hook_impl
    def app_exit(self, app):
        runtime = datetime.now() - self.appstart
        lgr.debug(f"Exit after {runtime}")
