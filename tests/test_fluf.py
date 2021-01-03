
import os, shutil

testfolder = os.path.expanduser('~/tmp/fluf_test')

import fluf  # NOQA E402
fluf.app.set_parameter('cache_path', os.path.join(testfolder, 'cache'))
fluf.app.set_parameter('publish_path', testfolder)


# remove old cache
if os.path.exists(testfolder):
    shutil.rmtree(testfolder)

# the make sure an empty folder exists:
os.makedirs(testfolder)


def test_test():
    assert True


def test_simple():

    @fluf.fluf()
    def t1():
        return 'a'

    rv = t1()
    assert rv == 'a'

    rv = t1()
    assert rv == 'a'


def test_check_cache():

    @fluf.fluf()
    def t2():
        return 'b'

    rv = t2()
    assert rv == 'b'

    # published filed:
    assert os.path.exists(os.path.join(testfolder, 't2.pkl'))

    # actual cached file:
    import glob
    cachefile = glob.glob(os.path.join(testfolder, 'cache', 't2.*.pkl'))
    assert len(cachefile) == 1


def test_does_it_rerun():

    tstfile = os.path.join(testfolder, 'test_does_it_rerun.touch')
    print(tstfile)
    if os.path.exists(tstfile):
        os.unlink(tstfile)

    @fluf.fluf()
    def t3():
        with open(tstfile, 'w') as F:
            F.write('x')
        return 'aa'

    #run & check outcome
    assert t3() == 'aa'

    # see if the tstfile was created
    assert os.path.exists(tstfile)

    # remove the testfile
    os.unlink(tstfile)

    # check it is gone
    assert not os.path.exists(tstfile)

    # rerun & check output
    # this time the output should be cached
    # the code not executed, and the tstfile
    # should not be recreated.
    assert t3() == 'aa'
    assert not os.path.exists(tstfile)
