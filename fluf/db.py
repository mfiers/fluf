
import atexit
from datetime import datetime
import logging
import os
import socket
import sys
import peewee as pw

from fluf import config
from fluf import helpers

lgr = logging.getLogger('FLUF.db')

DBPROXY = pw.DatabaseProxy()
DB = None


class Function(pw.Model):
    class Meta:
        database = DBPROXY

    checksum = pw.CharField(unique=True)
    name = pw.CharField()
    code = pw.TextField()

    @classmethod
    def init(cls, func):
        code, checksum = helpers.get_func_code_checksum(func)
        func, created = Function.get_or_create(
            code=code, checksum=checksum, name=func.__name__)
        if created:
            func.save()
        return func

    def get_call(self, name, args, kwargs):

        call_checksum = helpers.get_func_call_checksum(
            self.checksum, args, kwargs)
        fc, created = FunctionCall.get_or_create(
            function=self, checksum=call_checksum)
        if created:
            lgr.debug(f"created new fcall {fc}")
            fc.dirty = True
        fc.name = name
        fc.save()
        return fc

    def rich_str(self):
        return (f"[deep_sky_blue3]{self.name}[/deep_sky_blue3]:"
                f"[dark_sea_green4]{self.checksum[:4]}[/dark_sea_green4]")

    def __str__(self):
        return f"<fnc {self.name}:{self.checksum[:4]}>"


class FunctionCall(pw.Model):
    """ A unique call - combination of code + arguments """
    class Meta:
        database = DBPROXY

    function = pw.ForeignKeyField(Function, backref='calls')
    checksum = pw.CharField(unique=True)
    name = pw.CharField(null=True)
    dirty = pw.BooleanField(default=False)

    def rich_str(self):
        dirty = ' [bold orange_red1]dirty :t-rex:[/bold orange_red1]' if self.dirty else ''
        rv = (f"<fcl [deep_sky_blue3]{self.name}[/deep_sky_blue3]:"
              f"[dark_sea_green4]{self.checksum[:4]}[/dark_sea_green4]{dirty}>")
        return rv

    def __str__(self):
        dirty = ' dirty' if self.dirty else ''
        return (f"<fcl {self.name}:"
                f"{self.checksum[:4]}{dirty}>")

    def add_caller(self, caller):
        rv, created = FunctionCallFunction.get_or_create(
            caller=caller, called=self)
        if created:
            rv.save()
        return rv


class FunctionCallFunction(pw.Model):
    class Meta:
        database = DBPROXY
    caller = pw.ForeignKeyField(FunctionCall, backref='caller')
    called = pw.ForeignKeyField(FunctionCall, backref='called')
    dirty = pw.BooleanField(default=False)

    def __str__(self):
        dirty = '!' if self.dirty else ''
        return (f"<f2f {dirty}{self.caller.name}:"
                f"{self.caller.checksum[:4]} calls "
                f"{self.called.name}:"
                f"{self.called.checksum[:4]}>"
                )


class FunctionRun(pw.Model):
    class Meta:
        database = DBPROXY

    fcall = pw.ForeignKeyField(FunctionCall, backref='runs')
    time = pw.DateField()
    name = pw.CharField()
    runtime = pw.IntegerField()


class ScriptRun(pw.Model):
    """Represents one actual run of this script"""

    class Meta:
        database = DBPROXY

    checksum = pw.CharField(unique=True)
    hostname = pw.CharField()
    path = pw.CharField()
    start = pw.DateTimeField()

    @classmethod
    def init(cls, starttime):
        rv = ScriptRun(
            checksum=helpers.get_scriptrun_checksum(),
            hostname=socket.gethostname(),
            path=os.path.abspath(os.path.expanduser(sys.argv[0])),
            start=starttime,
        )
        rv.save()
        return rv

    def add_function(self, function):
        rv = ScriptRunFunction(
            scriptrun=self, function=function)
        rv.save()
        return rv

    def add_call(self, fcall):
        rv = ScriptRunFunctionCall(
            scriptrun=self, fcall=fcall,
            start=datetime.now()
        )
        rv.save()
        return rv

    def __str__(self):
        path_basename = os.path.basename(self.path)
        return (f"<fSrun {self.id} {self.hostname}:"
                f"{path_basename}:{self.checksum[:4]}>")


class ScriptRunFunction(pw.Model):
    """ An observation of a function object in this scriptrun """
    class Meta:
        database = DBPROXY

    scriptrun = pw.ForeignKeyField(ScriptRun, backref='srun_funcs')
    function = pw.ForeignKeyField(Function, backref='srun_funcs')


class ScriptRunFunctionCall(pw.Model):

    scriptrun = pw.ForeignKeyField(ScriptRun, backref='srun_fcalls')
    fcall = pw.ForeignKeyField(FunctionCall, backref='srun_fcalls')
    start = pw.DateTimeField()
    stop = pw.DateTimeField(null=True)
    action = pw.CharField(null=True)
    why_not_cache = pw.CharField(null=True)
    runtime = pw.FloatField(null=True)

    error = pw.TextField(null=True)
    success = pw.BooleanField(default=False)

    class Meta:
        database = DBPROXY

    def rich_str(self):
        from humanfriendly import format_timespan
        error = ""

        if self.runtime is not None:
            runtime = " in " + format_timespan(self.runtime, max_units=1)
        else:
            runtime = 'did not run'
        if self.error:
            error = " [red]ERROR :eggplant:[/red]"
        return f"< {self.scriptrun.id} {self.fcall.name} {self.action}{runtime}{error}>"

    def __str__(self):
        return f"< {self.scriptrun.id} {self.fcall} {self.action} >"


def instantiate():
    global DB
    script_checksum = helpers.get_scriptchecksum()
    db_file = os.path.join(config.FLUFCACHEFOLDER, f"{script_checksum}.db")
    DB = pw.SqliteDatabase(db_file, pragmas={'foreign_keys': 1})
    DBPROXY.initialize(DB)
    DB.create_tables([
        Function,
        FunctionCall,
        FunctionCallFunction,
        FunctionRun,
        ScriptRun,
        ScriptRunFunction,
        ScriptRunFunctionCall,
    ])


# ensure a clean exit
def exit_handler():
    global DB
    lgr.info("closing db")
    DB.close()

# def clean_dirty_records():

#     query = FunctionCallFunction.delete().where(
#         FunctionCallFunction.dirty)
#     lgr.info("removing %d f2f records", query.execute())

# #    query = FunctionCall.delete().where(
# #        FunctionCall.dirty)
# #    query.execute()
# #    lgr.info("removing %d fcall records", query.execute())

atexit.register(exit_handler)  # NOQA E305
