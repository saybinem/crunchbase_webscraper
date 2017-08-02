import os

import FrozenClass
import GenericWebScraper


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


class CBCompanyData(FrozenClass.RFrozenClass):
    def __init__(self, infile=None):
        super().__init__()
        if infile is not None:
            self.load(infile)
        else:
            self.json_file = str()
            self.company_id_vico = str()
            self.company_id_cb = str()
            self.completion_perc = float()
            self.overview = dict()
            self.company_details = CBCompanyDetails()
            self.people = list()
            self.advisors = list()
            self.past_people = list()
            self.error = str()
        self._freeze()

    def save(self, overwrite=False):
        assert (self.json_file != '')
        if not overwrite:
            assert (not os.path.isfile(self.json_file))
        out_dict = self.getDict()
        del out_dict['json_file']
        del out_dict['completion_perc']
        out_dict['company_details'] = self.company_details.serialize()
        # logging.info(GenericWebScraper.jsonPretty(self.getDict()))
        GenericWebScraper.saveJSON(out_dict, self.json_file)

    def load(self, json_file):
        in_dict = GenericWebScraper.readJSONFile(json_file)
        self.setDict(in_dict)
        self.company_details = CBCompanyDetails(in_dict['company_details'])
        self.json_file = json_file
