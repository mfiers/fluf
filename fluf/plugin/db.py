
from hashlib import sha256


import logging
import os
import sys

import peewee as pw

from fluf import models
from fluf.plugin import fluf_hook_impl
from fluf import util


# prevent logging from peewee
logging.getLogger('peewee').setLevel('WARNING')


lgr = logging.getLogger(__name__)
lgr.setLevel(logging.WARNING)


def get_db(app, script_uid):
    db_path = app.config['db_path']
    db_path = os.path.abspath(os.path.expanduser(db_path))
    if not os.path.exists(db_path):
        os.makedirs(db_path)
    db_file = os.path.join(db_path, f"{script_uid}.sqlite")
    db = pw.SqliteDatabase(db_file, pragmas={'foreign_keys': 1})
    models.db_proxy.initialize(db)
    db.create_tables(models.all_models)
    return db


class FlufDb():
    """ Database routines """

    @fluf_hook_impl
    def plugin_load(self, app):
        app.define_parameter('db_path', '~/.cache/fluf', str)
        app.define_parameter('hash_length', 10, int)


    @fluf_hook_impl
    def app_init(self, app):
        self.script_uid = util.get_script_uid(sys.argv[0])
        lgr.debug("Opening database for script "
                  f"with uid: {self.script_uid}")
        self.db = get_db(app, self.script_uid)
        self.hash_length = app.config['hash_length']

    @fluf_hook_impl
    def app_exit(self, app):
        lgr.debug("Closing database")
        self.db.close()

    @fluf_hook_impl
    def initialize_function(self, app, func):
        uid, code = util.get_func_uid_code(
            func, hash_length=self.hash_length)
        ffunc, _ = models.Function.get_or_create(
            uid=uid, code=code, name=func.__name__)
        ffunc.save()
        func.ffunc = ffunc
        lgr.debug(f"Register function {ffunc}")
        return ffunc


    @fluf_hook_impl
    def initialize_call(self, app, func, args, kwargs):

        call_uid = util.get_call_uid(func.ffunc, args, kwargs,
                                     hash_length=self.hash_length)
        fcall = func.ffunc.get_fcall(call_uid)
        fcall.add_args(args, kwargs)

        finvoc = fcall.get_invocation()

        lgr.debug(f"Created call: {fcall} {finvoc}")
        return fcall, finvoc
