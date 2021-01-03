

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


all = [FlufPickleType,
       FlufTextType,
       ]
