

import pickle


class FlufDataType():
    pass


class FlufPickleType(FlufDataType):
    name = 'pickle'
    extension = "pkl"

    @classmethod
    def saver(cls, obj, filename):
        with open(filename, 'wb') as F:
            pickle.dump(obj, F, protocol=4)

    @classmethod
    def loader(cls, filename):
        with open(filename, 'rb') as F:
            return pickle.load(F)


class FlufTextType(FlufDataType):
    name = 'text'
    extension = 'txt'

    @classmethod
    def saver(cls, obj, filename):
        with open(filename, 'w') as F:
            F.write(obj)

    @classmethod
    def loader(cls, filename):
        with open(filename, 'r') as F:
            return F.read()


class FlufMplType(FlufDataType):
    """ Save matplotlib plots to images """
    name = 'mpl'
    extension = 'png'

    @classmethod
    def saver(cls, obj, filename):
        import matplotlib.pyplot as plt
        if obj is None:
            obj = plt.gcf()
        obj.savefig(filename, bbox_inches='tight')
        plt.close()

    @classmethod
    def loader(cls, filename):
        #not really loading - don't expect ot need them anymore
        return None


class FlufTsvGzType(FlufDataType):
    """ Save matplotlib plots to images """
    name = 'tsvgz'
    extension = 'tsv.gz'

    @classmethod
    def saver(cls, obj, filename):
        import pandas as pd
        assert isinstance(obj, pd.DataFrame)
        obj.to_csv(filename, sep="\t")

    @classmethod
    def loader(cls, filename):
        #not really loading - don't expect ot need them anymore
        import pandas as pd
        return pd.read_csv(filename, sep="\t")



all = [FlufPickleType,
       FlufTextType,
       FlufMplType,
       FlufTsvGzType,
       ]
