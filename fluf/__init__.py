"""
Fluf -
"""

import atexit
from functools import wraps, partial
import logging

from .plugin import fluf_plugin_manager as fpm
from .plugin.logger import FlufLogger
from .plugin.executor import FlufExecutor
from .plugin.memcache import FlufMemcache
from .plugin.diskcache import FlufDiskcache
from .plugin.db import FlufDb
from .plugin.config import FlufConfig
from .plugin.calltracer import FlufCallTracer

from .app import FlufApp
from .cli import cli                              # NOQA F401

fpm.register(FlufLogger())
fpm.register(FlufExecutor())
fpm.register(FlufMemcache())
fpm.register(FlufDiskcache())
fpm.register(FlufCallTracer())
fpm.register(FlufDb())
fpm.register(FlufConfig())

app = FlufApp()

fpm.hook.plugin_load(app=app)
fpm.hook.load_config(app=app)
fpm.hook.app_init(app=app)

lgr = logging.getLogger(__name__)

# Ensure a clean exit
def exit_handler():
    fpm.hook.app_exit(app=app)
atexit.register(exit_handler)                     # NOQA E305


_prepare_run_called = False


def prepare_run():
    global _prepare_run_called
    if not _prepare_run_called:
        fpm.hook.prepare_run(app=app)
        _prepare_run_called = True


def fluf(**decorator_kwargs):
    """
    Main F function wrapper
    """

    def fluf_decorator(func):

        app.functions.append(func)

        # create /one/ function object - stored as func.ffunc
        # default action is in fluf.plugin.db
        fpm.hook.initialize_function(app=app, func=func,
                                     decorator_kwargs=decorator_kwargs)

        # do whatever is necessary
        fpm.hook.prepare_function(app=app, func=func,
                                  decorator_kwargs=decorator_kwargs)

        @wraps(func)
        def fluf_function_call(*args, **kwargs):

            prepare_run()  # ensure all is up to date

            fcall, finvoc = fpm.hook.initialize_call(
                app=app, func=func, args=args, kwargs=kwargs)

            fpm.hook.prepare_call(app=app, func=func, fcall=fcall,
                                  finvoc=finvoc, args=args,
                                  kwargs=kwargs)

            # Now somehow get the output of this function call!

            # here we call each plugin with which priority they want
            # to execute `get_result` - only the highest priority
            # (lowest number) gets executed
            #
            # Note: the key: `lambda x: x[0]` as key ensures only the
            # priority is used - second value is the plugin
            # otherwise - there would be a conflict if there are
            # hooks with the same priority - now it's just random
            priorities = sorted(fpm.hook.get_priority(
                app=app, func=func, fcall=fcall, finvoc=finvoc),
                                key=lambda x: x[0])

            assert priorities[0][0] < 100  # there must be one

            # remember who did the work
            finvoc.resolver = priorities[0][1].__class__.__name__

            # create a hookcaller for get_result with only one plugin
            # left

            hookcaller = fpm.subset_hook_caller(
                "get_result", remove_plugins=[x[1] for x
                                              in priorities[1:]])

            # and call it!
            rv = hookcaller(app=app, func=func, fcall=fcall,
                            finvoc=finvoc, args=args, kwargs=kwargs)

            if finvoc.success:
                fpm.hook.on_success_call(app=app, func=func, fcall=fcall,
                                         finvoc=finvoc, rv=rv)
                fcall.dirty = False
                lgr.info(f"{finvoc.resolver} {fcall}")
            else:
                fpm.hook.on_failed_call(app=app, func=func, fcall=fcall,
                                      finvoc=finvoc, rv=rv)
                fcall.dirty = True
                lgr.warning(f"FAIL {finvoc.resolver} {fcall}")

            fpm.hook.finish_call(app=app, func=func, fcall=fcall,
                                 finvoc=finvoc, rv=rv)

            finvoc.save()
            fcall.save()
            return rv

        # return the function wrapper
        return fluf_function_call

    # return the function decorator
    return fluf_decorator


# shortcut - cache to text
fluftxt = partial(fluf, datatype='text')
flufmpl = partial(fluf, datatype='mpl')
