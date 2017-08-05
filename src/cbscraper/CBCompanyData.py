import os
from cbscraper import FrozenClass
from cbscraper import GenericWebScraper
from cbscraper import CBCompanyDetails

class CBCompanyData(FrozenClass.RFrozenClass):
    def __init__(self, infile=None):
        super().__init__()
        if infile is not None:
            self._load(infile)
        else:
            self.json_file = str()
            self.company_id_vico = str()
            self.company_id_cb = str()
            self.completion_perc = float()
            self.overview = dict()
            self.company_details = CBCompanyDetails.CBCompanyDetails()
            self.people = list()
            self.advisors = list()
            self.past_people = list()
            self.founders = list()
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

    def _load(self, json_file):
        in_dict = GenericWebScraper.readJSONFile(json_file)
        self.setDict(in_dict)
        self.company_details = CBCompanyDetails.CBCompanyDetails(in_dict['company_details'])
        self.json_file = json_file
