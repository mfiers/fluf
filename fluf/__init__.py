"""
Fluf -
"""

import atexit
from dataclasses import dataclass
from functools import wraps

from .plugin import fluf_plugin_manager
from .plugin.logger import FlufLogger
from .plugin.executor import FlufExecutor
from .plugin.memcache import FlufMemcache


fluf_plugin_manager.register(FlufLogger())
fluf_plugin_manager.register(FlufExecutor())
fluf_plugin_manager.register(FlufMemcache())


# dummy class to store data & configuration data
@dataclass
class FlufAppData:
    functions = []


class FlufFuncData:
    pass


appdata = FlufAppData()
fluf_plugin_manager.hook.appinit(appdata=appdata)


# Ensure a clean exit
def exit_handler():
    fluf_plugin_manager.hook.appexit(appdata=appdata)
atexit.register(exit_handler)      # NOQA E305


def fluf():
    """
    Main F function wrapper
    """

    def fluf_decorator(func):

        func._fluf_data = FlufFuncData()  # store function specific data

        @wraps(func)
        def fluf_wrapper(*args, **kwargs):

            # here we call each plugin with which priority they want
            # to execute `get_result` - only the highest priority
            # (lowest number) gets executed
            priorities = sorted(
                fluf_plugin_manager.hook.get_priority(
                    appdata=appdata, func=func))

            # create a hookcaller for get_result with only one plugin left
            hookcaller = fluf_plugin_manager.subset_hook_caller(
                "get_result", remove_plugins=[x[1] for x in priorities[1:]])

            # and call it!
            rv = hookcaller(
                appdata=appdata, func=func, args=args, kwargs=kwargs)

            return rv

        # return the function wrapper
        return fluf_wrapper

    # return the function decorator
    return fluf_decorator
