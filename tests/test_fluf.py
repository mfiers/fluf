

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
