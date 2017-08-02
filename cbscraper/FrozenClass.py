from abc import ABCMeta, abstractmethod

class FrozenClass():

    __isfrozen = False

    def _freeze(self):
        self.__isfrozen = True

    def _genTypeErrorMsg(self, key, value):
        return "While trying " + str(key) + "=" + str(value) + ": " + str(self) \
               + " is a frozen class, "

    def __setattr__(self, key, value):
        if self.__isfrozen and not hasattr(self, key):
            raise TypeError(self._genTypeErrorMsg(key, value)+ "no new attributes allowed")
        object.__setattr__(self, key, value)

    def getDict(self):
        d = self.__dict__.copy()
        del d['_FrozenClass__isfrozen']
        return d

    def setDict(self, d):
        frstr = '_FrozenClass__isfrozen'
        if frstr in d:
            del d[frstr]
        self.__dict__ = d


class RFrozenClass():

    __isfrozen = False

    def _freeze(self):
        #logging.info("Setting __isfrozen to true in "+str(self))
        self.__isfrozen = True

    def _genTypeErrorMsg(self, key, value):
        return "While trying:\n " \
               + str(key) + " (" + str(type(key)) + ") \n = \n " \
               + str(value) + " (" + str(type(value)) + ") \n " \
               + "For " + str(self) \
               + " which is a R-frozen class, "

    def __setattr__(self, key, value):
        if self.__isfrozen:
            if not hasattr(self, key):
                raise TypeError(self._genTypeErrorMsg(key, value)+ "no new attributes allowed")
            if type(getattr(self, key)) != type(value):
                raise TypeError(self._genTypeErrorMsg(key, value)+ "can't change attribute type")
        object.__setattr__(self, key, value)

    def getDict(self):
        d = self.__dict__.copy()
        del d['_RFrozenClass__isfrozen']
        return d

    def setDict(self, d):
        frstr = '_RFrozenClass__isfrozen'
        if frstr in d:
            del d[frstr]
        self.__dict__ = d

class StringHolder(RFrozenClass, ABCMeta):

    @property
    @abstractmethod
    def valid_keys(self):
        pass

    def __init__(self, in_dict = None):
        super().__init__()
        if not in_dict:
            for key in self.valid_keys:
                self.__dict__[key] = ''
        else:
            del in_dict['_RFrozenClass__isfrozen']
            assert(set(in_dict.keys()) == self.valid_keys)
            for k in self.valid_keys:
                #logging.debug("Checking type of '"+k+"'")
                assert(type(in_dict[k]) == str)
            #logging.debug("Assigning dict")
            self.__dict__ = in_dict
        self._freeze()

    def serialize(self):
        return self.__dict__