
import copy
import inspect
import logging
import importlib.resources

import strictyaml as sy

import fluf.etc
from fluf.plugin import fluf_hook_impl

lgr = logging.getLogger(__name__)
lgr.setLevel(logging.DEBUG)


def get_default_config():

    # TODO: remove this - it is not really necessary - defaults are
    # specified upon parameter declaration in the code
    defconf = importlib.resources.read_text(fluf.etc, 'fluf_config.yaml')
    config = sy.load(defconf).data
    if 'function' not in config:
        config['function'] = {}

    if 'call' not in config:
        config['call'] = {}

    return config


class FlufConfig():
    """ Database routines """

    @fluf_hook_impl(tryfirst=True)
    def load_config(self, app):
        app.config = get_default_config()

        # see if parameters are defined in the main module
        frameinfo = inspect.stack()[-1]
        frameloc = frameinfo.frame.f_locals
        if 'fluf_config' in frameloc:
            app.config.update(frameloc['fluf_config'])

        app.validate_config()

    @fluf_hook_impl
    def prepare_function(self, app, func, decorator_kwargs):
        config = copy.deepcopy(app.config)
        config.update(decorator_kwargs)
        config = app.validate_config_custom(config)
        func.fconfig = config

    @fluf_hook_impl
    def prepare_call(self, app, func, fcall, finvoc, args, kwargs):
        update_config = {}
        for k, v in kwargs.items():
            if k.startswith('fluf_'):
                update_config[k[5:]] = v

        config = copy.deepcopy(func.fconfig)
        config.update(update_config)
        config = app.validate_config_custom(config)
        fcall.config = config
