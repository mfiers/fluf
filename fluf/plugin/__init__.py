
import pluggy


fluf_hook_spec = pluggy.HookspecMarker("fluf")
fluf_hook_impl = pluggy.HookimplMarker("fluf")


class FlufSpec:
    """ Fluf hook specification """

    @fluf_hook_spec
    def appinit(self, appdata):
        """ Initialization of the application """

    @fluf_hook_spec
    def init(self, appdata, func):
        """ Initialization of a function """

    @fluf_hook_spec
    def check(self):
        """ Check function prior to running """

    @fluf_hook_spec
    def get_priority(self, appdata, func):
        """ Advertise priority

            only the highest priority function will be called
            0 is very high, 100 is very low
            None means that this plugin does not want (or can)
            yield a result

        """

    @fluf_hook_spec(firstresult=True)
    def get_result(self, appdata, func, args, kwargs):
        """ Do something to retrieve the results - cache or execute """

    @fluf_hook_spec
    def prerun(self):
        """ prior to an actual run """

    @fluf_hook_spec
    def postrun(self):
        """ after an actual run """

    @fluf_hook_spec
    def appexit(self, appdata):
        """ Clean app exit """


fluf_plugin_manager = pluggy.PluginManager("fluf")
fluf_plugin_manager.add_hookspecs(FlufSpec)
