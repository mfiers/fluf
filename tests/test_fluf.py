
import os, shutil
import fluf

# cd to the correct tests folder
os.chdir(os.path.join(os.getcwd(), 'tests'))

# remove fluf cache
if os.path.exists('fluf'):
    shutil.rmtree('fluf')


def test_test():
    assert True


def test_simple():

    @fluf.cache()
    def t1():
        return 'a'

    rv = t1()
    assert rv == 'a'

    rv = t1()
    assert rv == 'a'



def test_check_cache():
    @fluf.cache()
    def t2():
        return 'b'

    rv = t2()
    assert rv == 'b'
    assert os.path.exists('fluf/t2.pkl')



def test_does_it_rerun():

    tstfile = 'test_does_it_rerun.touch'
    if os.path.exists(tstfile):
        os.unlink(tstfile)

    @fluf.cache()
    def t3():
        with open(tstfile, 'w') as F:
            F.write('x')
        return 'aa'

    #run & heck outcome
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
