from abc import ABCMeta, abstractmethod
import logging
import pprint

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


class RFrozenClass():

    __constructor_called = False
    __isfrozen = False

    def __init__(self):
        self.__constructor_called = True

    def _freeze(self):
        #logging.info("Setting __isfrozen to true in "+str(self))
        self.__isfrozen = True

    def _genTypeErrorMsg(self, key, value):
        return "While trying:\n " \
               + str(key) + " (" + str(getattr(self, key)) + ", " + str(type(getattr(self, key))) + ") \n = \n " \
               + str(value) + " (" + str(type(value)) + ") \n " \
               + "For " + str(self) \
               + " which is a R-frozen class, "

    def __setattr__(self, key, value):
        if self.__constructor_called and self.__isfrozen:
            if not hasattr(self, key):
                raise TypeError(self._genTypeErrorMsg(key, value)+ "no new attributes allowed")

            att = getattr(self, key)
            if not isinstance(value, type(att)):
                logging.info("att='" + str(att) + "'")
                logging.info(pprint.pformat(self.__dict__, indent=4))
                raise TypeError(self._genTypeErrorMsg(key, value)+ "can't change attribute type")
        object.__setattr__(self, key, value)

class StringHolder(RFrozenClass):

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