

from datetime import datetime
import logging

import peewee as pw

lgr = logging.getLogger(__name__)
lgr.setLevel(logging.WARNING)


db_proxy = pw.DatabaseProxy()


class BaseModel(pw.Model):
    class Meta:
        database = db_proxy

    def rstr(self):
        return str(self)


class Function(BaseModel):

    uid = pw.CharField(unique=True)
    name = pw.CharField()
    code = pw.TextField()
    created = pw.DateTimeField(default=datetime.now)
    historical = pw.BooleanField(default=False)

    def get_fcall(self, call_uid):
        call, _ = Call.get_or_create(
            uid=call_uid, function=self)
        call.historical = False

        call.save()
        return call

    def __str__(self):
        uid = str(self.uid)
        name = str(self.name)
        hist = ':H' if self.historical else ""
        return f"f/{name}/{uid[:4]}{hist}"

    def rstr(self):
        uid = str(self.uid)
        name = str(self.name)
        hist = ':[dark_orange3]H[/dark_orange3]' if self.historical else ""
        return f"[green]f/[green_yellow]{name}[/green_yellow]/{uid[:4]}{hist}[/]"



class Call(BaseModel):

    function = pw.ForeignKeyField(Function, backref='calls')
    uid = pw.CharField(unique=True)
    name = pw.CharField(null=True)
    historical = pw.BooleanField(default=False)
    dirty = pw.BooleanField(default=True)
    created = pw.DateTimeField(default=datetime.now)

    def add_caller(self, caller):
        rv, created = CallCall.get_or_create(
            caller=caller, called=self)
        if created or rv.historical:
            rv.historical = False
            rv.save()
        return rv

    def get_invocation(self):
        rv = Invocation.create(call=self)
        return rv

    def add_args(self, args, kwargs):
        for i, a in enumerate(args):
            CallArg.get_or_create(call=self, name=f'arg_{i:02d}',
                           val=str(a)[:100])
        for k, v in kwargs.items():
            CallArg.get_or_create(
                call=self, name=k, val=str(v)[:100])

    def __str__(self):
        flags = ''
        if self.historical:
            flags += 'H'
        if self.dirty:
            flags += 'D'
        if flags:
            flags = ':' + flags
        return (f"c/{self.function.name}/"
                f"{self.function.uid[:4]}/{self.uid[:4]}{flags}")

    def rstr(self):
        flags = ''
        if self.historical:
            flags += 'H'
        if self.dirty:
            flags += 'D'
        if flags:
            flags = f':[dark_orange3]{flags}[/dark_orange3]'
        return (f"[slate_blue3]c/[sky_blue3]{self.function.name}[/sky_blue3]/"
                f"{self.function.uid[:4]}/{self.uid[:4]}{flags}[/]")



class CallArg(BaseModel):

    call = pw.ForeignKeyField(Call, backref='args')
    name = pw.CharField()
    val = pw.CharField()

    def __str__(self):
        return f"@ca:{self.call.uid[:4]}:{self.name}={self.val}"


class CallCall(BaseModel):

    # the function call calling the other function
    caller = pw.ForeignKeyField(Call, backref='caller')

    # and the function call being called:
    called = pw.ForeignKeyField(Call, backref='called')
    historical = pw.BooleanField(default=False)

    def __str__(self):
        hist = ':H' if self.historical else ''
        return (f"@c2c:"
                f"{self.caller}>"
                f"{self.called}{hist}")


class Invocation(BaseModel):

    call = pw.ForeignKeyField(Call, backref='invocations')
    start = pw.DateTimeField(null=True)
    end = pw.DateTimeField(null=True)
    success = pw.BooleanField(default=False)
    resolver = pw.CharField(null=True, default='tbd')
    from_cache = pw.BooleanField(default=False)

    def addkeyval(self, key, val):
        return InvocationKeyVal.create(
            invocation=self, key=key, val=val)

    def __str__(self):
        suc = " Success!" if self.success else " Fail!"
        return f"@i:{self.call}:{self.start}{suc}"

class InvocationKeyVal(BaseModel):

    invocation = pw.ForeignKeyField(Invocation, backref='keyvals')
    key = pw.CharField()
    val = pw.CharField()


all_models = [Function, Call, CallArg, CallCall, Invocation, InvocationKeyVal]
