
import datetime
from hashlib import sha256
import inspect
import logging
import os
import socket
import sys

import dill

lgr = logging.getLogger('FLUF.helpers')

from fluf import config


def publish_file(cachefilename, pubfilename):
    """ publish a file - e.g. - hardlink from the cache
        folder to the workfolder
    """
    if os.path.exists(pubfilename):
        os.unlink(pubfilename)
    os.link(cachefilename, pubfilename)


def get_func_code_checksum(func):
    """ Calculate a per function call specific checksum """

    func_code = inspect.getsource(func).strip()

    hasher = sha256()
    hasher.update(func_code.encode())

    func_checksum = hasher.hexdigest()[:config.CHECKSUMLEN]
    lgr.debug(f"function checksum for {func.__name__} call is {func_checksum}")
    return func_code, func_checksum


def get_func_call_checksum(func_checksum, args, kwargs):
    hasher = sha256()
    hasher.update(func_checksum.encode())
    for a in args:
        hasher.update(dill.dumps(a))

    for k, v in sorted(kwargs.items()):
        hasher.update(dill.dumps(k))
        hasher.update(dill.dumps(v))

    call_checksum = hasher.hexdigest()[:config.CHECKSUMLEN]
    return call_checksum


def get_scriptrun_checksum():
    scriptrunchecksum = sha256()
    scriptrunchecksum.update(socket.gethostname().encode())
    scriptrunchecksum.update(
        datetime.datetime.now().isoformat().encode())
    return scriptrunchecksum.hexdigest()[:config.CHECKSUMLEN]


def get_scriptchecksum():
    hasher = sha256()
    hasher.update(socket.gethostname().encode())
    callscript = os.path.abspath(os.path.expanduser(sys.argv[0]))
    hasher.update(callscript.encode())
    checksum = hasher.hexdigest()[:config.CHECKSUMLEN]
    lgr.debug("Script: %s checksum %s", callscript, checksum)
    return checksum


#
# fluf configuration
#

def set_workfolder(workfolder):
    #if len(FUNCTIONS_OBSERVED) > 0:
    #    print("Must set workfolder before any fluf definitions")
    #    exit()
    config.WORKFOLDER = workfolder


def get_workfolder():
    return config.WORKFOLDER

def get_cachefolder():
    return os.path.join(get_workfolder(), 'fluf')


def set_publish_result(publish):
    config.DEFAULTPUBLISH = publish

def get_publish_result():
    return config.DEFAULTPUBLISH
