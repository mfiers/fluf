

from dataclasses import dataclass
from datetime import datetime
import logging

from fluf.plugin import fluf_hook_impl

lgr = logging.getLogger('__name__')


@dataclass
class FlufLoggerData:
    pass


class FlufLogger():
    """ Function execution logger """

    @fluf_hook_impl
    def appinit(self, appdata):
        lgr.debug("Start")
        self.data = appdata.logger = FlufLoggerData()
        self.data.appstart = datetime.now()


    @fluf_hook_impl
    def appexit(self, appdata):
        runtime = datetime.now() - self.data.appstart
        lgr.debug(f"Exit after {runtime}")
        self.data = appdata.logger = FlufLoggerData()
        self.data.appstart = datetime.now()
