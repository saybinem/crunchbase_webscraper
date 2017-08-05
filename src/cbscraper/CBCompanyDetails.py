import json

class CBCompanyDetails():
    def __init__(self):
        super().__init__()
        self.founded = str()
        self.closed = str()
        self.email = str()
        self.employees_num = str()
        self.employees_found = str()
        self.phone_number = str()
        self.description = str()
        #self._freeze()