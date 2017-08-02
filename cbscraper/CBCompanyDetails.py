import FrozenClass

class CBCompanyDetails(FrozenClass.RFrozenClass):
    def __init__(self, in_dict=None):
        super().__init__()
        if in_dict is None:
            self.founded = str()
            self.closed = str()
            self.email = str()
            self.employees_num = str()
            self.employees_found = str()
            self.phone_number = str()
            self.description = str()
        else:
            valid_keys = {'founded', 'closed', 'email', 'employees_num', 'employees_found', 'phone_number', 'description'}
            assert (set(in_dict.keys()) == valid_keys)
            self.setDict(in_dict)
        self._freeze()

    def serialize(self):
        return self.getDict()