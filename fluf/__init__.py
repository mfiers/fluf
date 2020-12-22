
from datetime import datetime
from functools import partial, wraps
import inspect
import itertools
import logging
import os
import socket
import sys
import time


import dill


from .flufio import pickle_loader, pickle_saver
from .flufio import mpl_loader, mpl_saver
from .flufio import txt_loader, txt_saver
from .memcache import insert_memcache, from_memcache, in_memcache
from .helpers import publish_file, set_workfolder, get_workfolder, \
    get_cachefolder, get_func_code_checksum
import fluf.db as db
import fluf.config as config


db.instantiate()

lgr = logging.getLogger('FLUF')
lgr.setLevel(logging.INFO)

lgr_callstack = logging.getLogger('FLUF.callstack')
lgr_callstack.setLevel(logging.INFO)


#
# globals
#

DEFAULTPUBLISH = True
CHECKSUMLEN = 10

FUNCTIONS_OBSERVED = set()
CACHENAMES = set()
PUBLISHED = []
CALLHISTORY = []


# fluf workflows are meant to be simple - so one main script is responsible
# the checksum of that script is the call database

STARTTIME = datetime.now()

_RUN = None


def get_scriptrun_object():
    global _RUN
    if _RUN is None:
        _RUN = db.ScriptRun.init(STARTTIME)
    return _RUN


def cache(cachename=None,
          extension='pkl',
          loader=pickle_loader,
          saver=pickle_saver,
          publish=None,
          cache=True,
          diskcache=True,
          memcache=8):

    # globals for later use
    workfolder = get_workfolder()
    cachefolder = get_cachefolder()

    if publish is None:
        publish = DEFAULTPUBLISH

    if not os.path.exists(cachefolder):
        os.makedirs(cachefolder)

    def cache_decorator(func):

        func.ffunc = db.Function.init(func)
        func.scriptrun = get_scriptrun_object()
        func.scriptrun.add_function(func.ffunc)

        @wraps(func)  # so we don't lose function sign.
        def _fluf_func_wrapper(*args, **kwargs):

            publish_this_call = kwargs.get('_publish', publish)

            # determine the basename of this function call
            if '_cachename' in kwargs:
                basename = kwargs['_cachename']
            elif cachename is not None:
                basename = cachename
            else:
                basename = func.__name__

            CACHENAMES.add(basename)  # TODO: move this to the db

            fcall = func.ffunc.get_call(basename, args, kwargs)
            srun_fcall = func.scriptrun.add_call(fcall)  # for logging

            cfbase = fcall.checksum + '.' + basename + '.' + extension
            pubname = basename + '.' + extension
            cachefilename = os.path.join(cachefolder, cfbase)
            pubfilename = os.path.join(workfolder, pubname)


            if publish_this_call:
                if pubfilename in PUBLISHED:
                    lgr.critical("Duplicate publish name - " +
                                 "they will be overwritten")

            lgr.debug(f"final cache file name is {cachefilename}")

            action_taken = None
            why_not_use_diskcache = ""


            if cache:
                # we do try to use the cache

                if in_memcache(fcall):
                    lgr.debug("<M Return from memcache %s %s",
                             basename, fcall)
                    # if already im memcache - we assume the file was
                    # published - so do not check here
                    action_taken = 'memcache'

                    # value to return
                    rv = from_memcache(fcall)

                elif diskcache:
                    # attempt retrieval from diskache

                    # we only check the callstack when accessing diskcache
                    # assume that there is no metaprogramming - hence - if something
                    # is in memcache - the code cannot have changed.

                    # first prepare callstack to see if there are code changes
                    prep_callstack(func)

                    diskcache_exist = os.path.exists(cachefilename)
                    diskcache_notzero = os.stat(cachefilename).st_size > 0 \
                        if diskcache_exist else False

                    if not diskcache_exist:
                        why_not_use_diskcache = 'does not exist'
                        lgr.debug("Not using diskcache - cachefile does not exist")
                    elif not diskcache_notzero:
                        why_not_use_diskcache = 'cache filesize zero'
                        lgr.debug("Not using diskcache - cachefile is empty")
                    elif fcall.dirty:
                        why_not_use_diskcache = 'fcall dirty'
                        lgr.debug("Not using diskcache - callstack  not valid")

                    if (diskcache_exist and diskcache_notzero
                                        and (not fcall.dirty)):  # NOQA E127

                        action_taken = 'diskcache'
                        lgr.debug(f"<D Return from diskcache {fcall}")
                        rv = loader(cachefilename)
                        insert_memcache(fcall, rv)

                    else:
                        lgr.debug(f"Not using diskcache because: "
                                  f"'{why_not_use_diskcache}': %s %s",
                                  basename, fcall)

            if action_taken is None:

                # it appears we've not found anything to return yet
                # - so - we'll have to re-run the function
                lgr.debug("<R (re)running function: %s %s",
                          basename, fcall)
                action_taken = 'run'

                # when calling this function - see what is called
                # so we can recall later if all parent bits have not
                # changed

                rv = func(*args, **kwargs)
                if cache and diskcache and cachefilename is not None:
                    lgr.debug("caching to: %s", cachefilename)
                    saver(rv, cachefilename)
                insert_memcache(fcall, rv)

            store_callstack(fcall)
            if publish_this_call:
                publish_file(cachefilename, pubfilename)
            srun_fcall.action = action_taken
            srun_fcall.why_not_cache = why_not_use_diskcache
            srun_fcall.stop = datetime.now()
            srun_fcall.runtime = (srun_fcall.stop - srun_fcall.start).total_seconds()
            srun_fcall.save()
            fcall.dirty = False
            fcall.save()
            lgr.info(f"Function {fcall} - {action_taken}")
            return rv

        return _fluf_func_wrapper
    return cache_decorator


def store_callstack(fcall):
    lgr.debug(f'investigate callstack of "{fcall}"')
    for frameinfo in inspect.stack()[2:]:
        # skip the first two entries
        #   - entry one is this function
        #   - entry two is the calling fcuntion (which is already in fcall)

        frameloc = frameinfo.frame.f_locals
        if frameinfo.function != '_fluf_func_wrapper':
            continue
        if 'fcall' not in frameloc:
            continue
        fcaller = frameloc['fcall']
        if fcaller == fcall:
            continue
        fcall.add_caller(fcaller)
        lgr.debug(f"{fcall} called by {fcaller}")
        break  # only store immediate caller function


def print_state(func):
    ffunc = func.ffunc
    srun = func.scriptrun
    # funcs_in_this_run = [srf.function for srf in srun.srun_funcs]

    # print(f"State of function: {ffunc} {srun}")
    # dirty_calls = []
    # affected_calls = []
    # affected_relations = []

    # def find_affected(fcall):
    #     rfunc = fcall.function
    #     dirty = rfunc not in funcs_in_this_run
    #     if dirty:
    #         dirty_calls.append(fcall)
    #         affected_calls.append(fcall)

    #     any_called_dirty = False
    #     for fcaller in fcall.caller:
    #         if find_affected(fcaller.called):
    #             # caller is affected - we are affected
    #             any_called_dirty = True
    #             affected_relations.append(fcaller)

    #     if any_called_dirty:
    #         affected_calls.append(fcall)

    #     return any_called_dirty or dirty

    # for fcall in ffunc.calls:
    #     find_affected(fcall)

    # # for d in dirty_calls:
    # #     print('dirty', d)
    # # for d in affected_calls:
    # #     print('affected', d)
    # # for d in affected_relations:
    # #     print('affected relation', d)

    def print_call(prefix, fcall):
        print(prefix, fcall)
        for fcaller in fcall.caller:
            print_call("  " + prefix, fcaller.called)

    for fcall in ffunc.calls:
        print_call("", fcall)


def prep_callstack(func, delete_relations=True):
    ffunc = func.ffunc
    srun = func.scriptrun
    funcs_in_this_run = [srf.function for srf in srun.srun_funcs]

    affected_relations = []

    with db.DB.atomic():
        def find_affected(fcall):
            rfunc = fcall.function
            dirty = rfunc not in funcs_in_this_run
            if dirty:
                fcall.dirty = True

            any_called_dirty = False
            for fcaller in fcall.caller:
                if find_affected(fcaller.called):
                    any_called_dirty = True
                    affected_relations.append(fcaller)
                    fcall.dirty = True

            fcall.save()

            return any_called_dirty or dirty

        #lgr.info("Prep callstack: %d calls dirty, %d calls affected, %d relations affected",
        #         len(dirty_calls), len(affected_calls), len(affected_relations))

        for fcall in ffunc.calls:
            find_affected(fcall)

        if delete_relations:
            for r in affected_relations:
                r.delete_instance()


def print_db_dump():

    for fnc in db.Function.select():
        print('|', fnc)
        for fcl in db.FunctionCall.select()\
            .where(db.FunctionCall.function == fnc):
            print('| |', fcl)
            for f2f in db.FunctionCallFunction.select()\
                .where(db.FunctionCallFunction.caller == fcl):
                print('| | |', f2f)

    lastrun = db.ScriptRun.select().order_by(-db.ScriptRun.start).get()
    for c in db.ScriptRun.select().order_by(-db.ScriptRun.start).limit(3):
        is_lastrun = '*' if c == lastrun else ''
        print('scrpt:', is_lastrun + str(c), c.start)

    for c in db.ScriptRunFunction.select()\
        .where(db.ScriptRunFunction.scriptrun == lastrun):
        print('srun_function  ', c, c.function)
    for c in db.ScriptRunFunctionCall.select()\
        .where(db.ScriptRunFunctionCall.scriptrun == lastrun)\
        .order_by(db.ScriptRunFunctionCall.start):
        print('srun_fcall ', c, c.runtime, c.why_not_cache)
#    fluf.print_run_info(test5)


def print_run_info(func):
    ffunc = func.ffunc
    srun = func.scriptrun
    print(f"Function: {ffunc} {srun}")

    SRFC = db.ScriptRunFunctionCall
    def print_call(prefix, fcall):
        sfcall = SRFC.select().where(
            SRFC.fcall == fcall).get()
        print(prefix, fcall.name, fcall) #, sfcall)
        for fcaller in fcall.caller:
            print_call("  " + prefix, fcaller.called)
    for fcall in ffunc.calls:
        print_call("->", fcall)

# def get_called(caller):

#     for rec in dbcursor.execute(
#             """SELECT called_name, called_objhash, called_calldefhash
#                FROM calls
#                WHERE caller_calldefhash = ?""",
#             (caller.calldefhash, )):

#         called = function_call(name=rec[0], objhash=rec[1], calldefhash=rec[2])
#         yield caller.name, called
#         if caller.objhash != called.objhash:
#             yield from get_called(called)


# def get_called_obj(fname, objhash):

#     for rec in dbcursor.execute(
#             """SELECT called_name, called_objhash, called_calldefhash
#                FROM calls
#                WHERE caller_objhash = ?""",
#             (objhash, )):

#         called = function_call(name=rec[0], objhash=rec[1], calldefhash=rec[2])
#         yield fname, called
#         if objhash != called.objhash:
#             yield from get_called_obj(called.name, called.objhash)

# def print_obj_callstack(func):
#     print(dir(func))
#     return
#     for o in get_called_obj(func._fluf_name, func._fluf_objhash):
#         print(o)



# def check_call_stack(caller):
#     return

#     lgr_callstack.debug('$ check callstack for call "%s" obj:%s call:%s ',
#                         caller.name, caller.objhash, caller.calldefhash)

#     nothing_changed = True
#     self_call_found = False

#     for _cn, called in get_called(caller):
#         #print('!!!!', caller.name, _cn, called.name, called.objhash)
#         if called.objhash == caller.objhash:
#             # ~~~ should alwasy be there
#             self_call_found = True
#         function_still_present = called.objhash in OBJHASHES
#         if function_still_present:
#             lgr_callstack.debug(
#                 "  - called %s obj:%s still ok",
#                                 called.name, called.objhash)
#         else:
#             lgr_callstack.info("!Change in callstack for %s: %s obj:%s !!!",
#                                caller.name, called.name, called.objhash)
#             nothing_changed = False
#             # remove this caller record from callstack
#             # the stack is not complete - so need to rerun
#             dbcursor.execute(
#                 """DELETE FROM calls
#                          WHERE caller_objhash = ?
#                            AND caller_calldefhash = ?
#                            AND called_objhash = ? """,
#                 (caller.objhash, caller.calldefhash, called.objhash))
#             break

#     if not self_call_found:
#         lgr.info("no callstack record of this run?")
#         # unsure if this should be the case - but we cannot validate that the
#         # callstack has changed - so best advise rerun
#         return False

#     # else - if no called code has changed - keep it as is
#     return nothing_changed

mplcache = partial(cache, extension='png', loader=mpl_loader, saver=mpl_saver)


txtcache = partial(cache, extension='txt', loader=txt_loader, saver=txt_saver)
