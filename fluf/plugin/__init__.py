
import pluggy


fluf_hook_spec = pluggy.HookspecMarker("fluf")
fluf_hook_impl = pluggy.HookimplMarker("fluf")


class FlufSpec:
    """ Fluf hook specification """

    @fluf_hook_spec
    def plugin_load(self, app):
        """ time to define configuration options """

    @fluf_hook_spec
    def load_config(self, app):
        """ Initialization of the application """

    @fluf_hook_spec
    def app_init(self, app):
        """ Initialization of the application """

    @fluf_hook_spec(firstresult=True)
    def initialize_function(self, app, func, decorator_kwargs):
        """
        Initialize function & function data storage
        Should be only one function doing this - default
        in `plugin.db`
        """

    @fluf_hook_spec
    def prepare_function(self, app, func, decorator_kwargs):
        """ Check function prior to running """

    @fluf_hook_spec
    def prepare_run(self, app):
        """
        Prepare for running

        Should be called only once - after all fucntions are loaded
        """

    @fluf_hook_spec(firstresult=True)
    def initialize_call(self, app, func, args, kwargs):
        """
        Initialize function call &  data storage
        Should be only one function doing this
        """

    @fluf_hook_spec
    def finish_call(self, app, func, fcall, finvoc, rv):
        """ Check function prior to running """

    @fluf_hook_spec
    def post_call(self, app, func, fcall, finvoc, args, kwargs, rv):
        """ Check function prior to running """

    @fluf_hook_spec
    def get_priority(self, app, func, fcall, finvoc):
        """Advertise resolve priority

        Only the highest priority function will be called 0 is very
        high, 99 is very low. A value of 100 (or more) will neve be
        called

        """
    @fluf_hook_spec
    def on_success_call(self, app, func, fcall, finvoc, rv):
        """On a successfull call """
    @fluf_hook_spec
    def on_failed_call(self, app, func, fcall, finvoc, rv):
        """On a failed call """

    @fluf_hook_spec(firstresult=True)
    def get_result(self, app, func, fcall, finvoc, args, kwargs):
        """ Do something to retrieve the results"""

    @fluf_hook_spec
    def prerun(self):
        """ prior to an actual run """

    @fluf_hook_spec
    def postrun(self):
        """ after an actual run """

    @fluf_hook_spec
    def app_exit(self, app):
        """ Clean app exit """


fluf_plugin_manager = pluggy.PluginManager("fluf")
fluf_plugin_manager.add_hookspecs(FlufSpec)
