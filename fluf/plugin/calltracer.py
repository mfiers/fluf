
import inspect
import logging

from fluf.plugin import fluf_hook_impl
from fluf import models as fm

lgr = logging.getLogger(__name__)
#lgr.setLevel(logging.DEBUG)
lgr.setLevel(logging.INFO)

DEBUG = True


class FlufCallTracer:
    """ Database routines """

    def print_callstack(self, f):
        from rich import print as rprint

        # in case we're past an actual function, and not a ffunc record
        if not isinstance(f, fm.Function) and hasattr(f, 'ffunc'):
            f = f.ffunc

        def cp(prefix, c):
            rprint(f"{prefix}  [slate_blue3]+ CALL:[/] "
                   f"{c.rstr()} | {c.function.rstr()}")
            for cc in fm.CallCall\
                        .select()\
                        .join(fm.Call, on=fm.CallCall.called)\
                        .where(fm.CallCall.caller == c,
                               ~fm.CallCall.historical,
                               ~fm.CallCall.called.historical):
                cp(prefix + '  ', cc.called)

        rprint(f'## [green]FUNC: [/]{f.rstr()}')
        for c in fm.Call.select()\
                        .join(fm.Function)\
                        .where(fm.Call.function == f):
            cp("", c)

    @fluf_hook_impl
    def app_init(self, app):
        # expose print_callstack to the outer world
        app.api.print_callstack = self.print_callstack

    @fluf_hook_impl
    def prepare_run(self, app):

        # print("prepare run")
        # first mark all functions which are not in this script as
        # historical - and vice versa
        all_ffunc_in_code = set([f.ffunc for f in app.functions])
        for a in all_ffunc_in_code:
            a.historical = False
            a.save()

        all_ffunc_known = set(
            fm.Function.select().where(~fm.Function.historical))

        if False:
            print('<' * 80)
            for a in all_ffunc_in_code:
                self.print_callstack(a)
            print('<' * 80)

        for func in all_ffunc_known - all_ffunc_in_code:
            # ensure that all functions that dissapeared
            # become historical
            lgr.info(f"Found a change in function: {func.name}")
            func.historical = True
            func.save()

        # and iteratively make all calls dirty that call this function
        def historify(c):
            for cc in fm.CallCall\
                        .select()\
                        .join(fm.Call, on=fm.CallCall.caller)\
                        .where(fm.CallCall.called == c,
                               ~fm.Call.historical,
                               ~fm.CallCall.historical):
                lgr.debug(f'make dirty because callstack: '
                          f'{call}')
                if cc.called.historical:
                    cc.historical = True
                    cc.save()
                cc.caller.dirty = True
                cc.caller.save()
                historify(cc.caller)

        # now find all historical functions & ensure associated calls
        # become historical as well
        for call in fm.Call.select().join(fm.Function)\
                                    .where(
                                        fm.Function.historical,
                                        ~fm.Call.historical ):
            lgr.debug(f'make dirty&historical because function '
                      f'changed: {call}')
            call.historical = True
            call.dirty = True
            historify(call)
            call.save()

    #@fluf_hook_impl
    ##def prepare_call(self, app, func, fcall, finvoc, args, kwargs):
    #    self.print_callstack(func.ffunc)

    @fluf_hook_impl
    def on_success_call(self, app, func, fcall, finvoc, rv):

        lgr.debug(f'Successfully called {fcall} - fix up callstack')
        # skip the first entry - that is this function
        flufcalls_seen = 0
        fcall.dirty = False

        # ensure we record the first function calling this function
        for frameinfo in inspect.stack()[:]:

            if frameinfo.function == 'fluf_function_call':
                flufcalls_seen += 1

                # the first time we hit a function called fluf_function_call it
                # is still this functioncall - ignore
                # print('ff', flufcalls_seen)
                if flufcalls_seen < 2:
                    continue

                frameloc = frameinfo.frame.f_locals

                # - entry two is the calling fcuntion (which is
                # already in fcall) print('-' * 80)
                # print(frameinfo.function, frameinfo.filename)
                # print('fcall' in frameloc)
                fcaller = frameloc['fcall']
                assert fcaller != fcall
                call2call = fcall.add_caller(fcaller)
                lgr.debug(f"Add Call Link: {call2call}")

                return
