#
# MEMCACHE
#



import logging

from collections import defaultdict

lgr_memcache = logging.getLogger('FLUF.memcache')
lgr_memcache.setLevel(logging.INFO)


MEMCACHE = defaultdict(list)


def insert_memcache(fcall, rv):
    global MEMCACHE
    lgr_memcache.debug(f"Insert into memcache: {fcall}")
    MEMCACHE[fcall.function.checksum].append((fcall.checksum, rv))


def from_memcache(fcall):
    for k, v in MEMCACHE[fcall.function.checksum]:
        if k == fcall.checksum:
            lgr_memcache.debug(
                f"Returning from memcache: {fcall}")
            return v


def in_memcache(fcall):
    lgr_memcache.debug(f'check if fcall {fcall} in memcache')
    if fcall.function.checksum in MEMCACHE:
        for a, b in MEMCACHE[fcall.function.checksum]:
            if a == fcall.checksum:
                lgr_memcache.debug(f"Found in memcache: {fcall}")
                return True
    else:
        lgr_memcache.debug(f"Not in memcache: {fcall}")
        return False
