

import logging
import pickle


lgr = logging.getLogger(__name__)


def pickle_loader(filename):
    with open(filename, 'rb') as F:
        return pickle.load(F)


def pickle_saver(obj, filename):
    with open(filename, 'wb') as F:
        pickle.dump(obj, F, protocol=4)


def mpl_saver(obj, filename):
    import matplotlib.pyplot as plt
    if obj is None:
        obj = plt.gcf()
    lgr.info("saving image to %s", filename)
    obj.savefig(filename, format='png', bbox_inches='tight')
    plt.close()


def mpl_loader(filename):
    """ we really never want to load an image again """
    return None


def txt_saver(obj, filename):
    with open(filename, 'w') as F:
        F.write(obj)


def txt_loader(filename):
    with open(filename) as F:
        return F.read()
