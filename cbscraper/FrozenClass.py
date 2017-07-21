class FrozenClass():
    __isfrozen = False

    def _freeze(self):
        self.__isfrozen = True

    def __setattr__(self, key, value):
        if self.__isfrozen and not hasattr(self, key):
            raise TypeError("%r is a frozen class, no new attributes allowed" % self)
        object.__setattr__(self, key, value)


class RFrozenClass():
    __isfrozen = False

    def _freeze(self):
        self.__isfrozen = True

    def __setattr__(self, key, value):
        if self.__isfrozen:
            if not hasattr(self, key):
                raise TypeError("%r is a r-frozen class, no new attributes allowed" % self)
            if type(getattr(self, key)) != type(value):
                raise TypeError("%r is a r-frozen class, you can't change the type of an attribute" % self)
        object.__setattr__(self, key, value)