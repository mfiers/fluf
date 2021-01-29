
from hashlib import sha256
import inspect
import os

import dill


def path_validate(pth):
    pth = os.path.abspath(os.path.expanduser(pth))
    return pth


def get_script_uid(scriptfile):
    fullpath = os.path.realpath(
        os.path.abspath(
            os.path.expanduser(scriptfile)))
    hasher = sha256()
    hasher.update(fullpath.encode())
    return 's' + hasher.hexdigest()[:10]


def get_call_uid(ffunc, args, kwargs, hash_length):
    """ Generate a call hash """
    hasher = sha256()
    hasher.update(ffunc.uid.encode())
    for a in args:
        hasher.update(dill.dumps(a, protocol=4))

    for k, v in sorted(kwargs.items()):
        hasher.update(dill.dumps(k, protocol=4))
        hasher.update(dill.dumps(v, protocol=4))

    call_uid = 'c' + hasher.hexdigest()[:hash_length]
    # lgr.debug("Call UID: %s", call_uid)

    return call_uid


def get_func_uid_code(func, hash_length):

    func_code = inspect.getsource(func).strip()

    # I would like to do some simple cleaning to not not have the
    # hash change due to whitespace & comments otherwise functions
    # are re-executed with every space changed
    # TODO: improve on this

    hasher = sha256()
    hasher.update(func_code.encode())

    # TODO: make hash length configurable?
    func_uid = 'f' + hasher.hexdigest()[:hash_length]
    # lgr.debug(f"Function UID is {func._fluf.func_uid}")

    return func_uid, func_code
