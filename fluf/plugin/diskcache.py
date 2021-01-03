

import logging
import os

from fluf.plugin import fluf_hook_impl
import fluf.datatypes as datatypes
from fluf.util import path_validate

lgr = logging.getLogger(__name__)
lgr.setLevel(logging.INFO)
# lgr.setLevel(logging.DEBUG)


def datatype_validate(obj):
    if isinstance(obj, str):
        return obj
    if issubclass(obj, datatypes.FlufDataType):
        return obj
    raise TypeError(f"{obj} is invalid")


class FlufDiskcache():
    """ Function execution diskcache """

    @fluf_hook_impl
    def plugin_load(self, app):

        # define parameters
        app.define_parameter('cache_path', 'fluf/cache', path_validate)
        app.define_parameter('publish_path', 'fluf/', path_validate)

        def _validate_method(x):
            assert x in ['link', 'symlink']
            return x
        app.define_parameter('publish_method', 'link', _validate_method)
        app.define_parameter('datatype', datatypes.FlufPickleType,
                             datatype_validate)
        app.define_parameter('diskcache', True, bool)
        app.define_parameter('publish', True, bool)
        app.define_parameter('cachename', "<function_name>", str)

        for dt in datatypes.all:
            app.register_datatype(dt)

    def get_datatype(self, app, datatype):
        if isinstance(datatype, str) and datatype in app.datatypes:
            return app.datatypes[datatype]
        elif issubclass(datatype, datatypes.FlufDataType):
            return datatype

        lgr.warning(f"invalid datatype: {datatype}")
        raise Exception()

    def get_cache_name(self, app, func, fcall):
        conf = func.fconfig
        cachepath = conf['cache_path']
        if not os.path.exists(cachepath):
            os.makedirs(cachepath)
        datatype = self.get_datatype(app, conf['datatype'])
        cachename = conf['cachename']
        if cachename == "<function_name>":
            cachename = func.__name__

        lgr.debug(f"diskcache {fcall} {datatype.name} {cachepath}")
        cachefile = os.path.join(cachepath,
                                 f"{cachename}.{fcall.uid}"
                                 f".{datatype.extension}")
        return cachefile

    def get_publish_name(self, app, func, fcall):
        """ Determine path to publish the file to """
        conf = func.fconfig
        publishpath = conf['publish_path']
        if not os.path.exists(publishpath):
            os.makedirs(publishpath)
        datatype = self.get_datatype(app, conf['datatype'])
        cachename = conf['cachename']
        if cachename == "<function_name>":
            cachename = func.__name__

        lgr.debug(f"diskcache publish to {fcall} {datatype.name} {publishpath}")
        publishfile = os.path.join(publishpath,
                                   f"{cachename}"
                                   f".{datatype.extension}")
        return publishfile

    @fluf_hook_impl
    def get_priority(self, app, func, fcall, finvoc):
        """ only run when in memcache - but then with high priority """

        lgr.debug(f"Use diskcache for call {fcall}?")
        lgr.debug(f"  - discache in config: {func.fconfig['diskcache']}")
        lgr.debug(f"  - call dirty?: {fcall.dirty}")
        if not func.fconfig['diskcache']:
            # no caching
            lgr.debug(f"no diskcache - priority 1000 for {fcall}")
            return 1000, self

        if fcall.dirty:
            # no caching
            lgr.debug(f"Not using diskcache - {fcall} is dirty")
            return 1000, self

        cachefile = self.get_cache_name(app, func, fcall)
        if not os.path.exists(cachefile):
            lgr.debug(f"cachefile not found -priority 1000 for {fcall}")
            return 1000, self

        # we can do this!
        lgr.debug(f"Diskcache file found for {fcall}")
        return 30, self

    @fluf_hook_impl
    def get_result(self, app, func, fcall, finvoc, args, kwargs):
        conf = func.fconfig
        datatype = self.get_datatype(app, conf['datatype'])
        cachefile = self.get_cache_name(app, func, fcall)
        basename = os.path.basename(cachefile)
        dtype = datatype.name
        lgr.debug(f"Load cached {fcall} from disk {dtype}:{basename}")
        try:
            rv = datatype.loader(cachefile)
            finvoc.success = True
            finvoc.from_cache = True
            return rv
        except:
            finvoc.success = False
            fcall.dirty = True
            finvoc.save()
            fcall.save()
            raise
        return rv


    @fluf_hook_impl
    def on_success_call(self, app, func, fcall, finvoc, rv):
        conf = func.fconfig
        if not conf['diskcache']:
            # do nothing
            # lgr.debug(f"not caching to disk {fcall}")
            return

        lgr.debug(f"store data from {fcall} in diskcache")
        datatype = self.get_datatype(app, conf['datatype'])
        cachefile = self.get_cache_name(app, func, fcall)
        datatype.saver(rv, cachefile)

        if conf['publish']:
            pmethod = conf['publish_method']
            publishfile = self.get_publish_name(app, func, fcall)
            if os.path.exists(publishfile):
                os.unlink(publishfile)
            if pmethod == 'link':
                lgr.debug(f'publish link to output: {publishfile}')
                os.link(cachefile, publishfile)
            elif pmethod == 'symlink':
                lgr.debug(f'publish symlink to output: {publishfile}' )
                os.symlink(cachefile, publishfile)




    # @fluf_hook_impl
    # def get_priority(self, app, func, fcall, finvoc):
    #     """ only run when in diskcache - but then with high priority """
    #     return 1000, self
    #     # if fcall.uid in self.data:
    #     #    return 500, self
    #     #else:
    #     #    return 1000, self

    # @fluf_hook_impl
    # def get_result(self, app, func, fcall, args, kwargs):
    #     lgr.debug("Return from memcache")
    #     return self.data[fcall.uid]

    # @fluf_hook_impl
    # def post_call(self, app, func, fcall, args, kwargs, rv):
    #     lgr.debug(f"store in memcache {fcall}")
    #     self.data[fcall.uid] = rv
