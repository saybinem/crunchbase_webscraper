import os

from cbscraper import GenericWebScraper
from cbscraper import CBCompanyDetails
import json

class CBCompanyData():
    def __init__(self):
        super().__init__()
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
        #self._freeze()

    def save(self, outfile, overwrite=False):
        if not overwrite:
            assert (not os.path.isfile(outfile))
        GenericWebScraper.saveJSON(self, outfile)

    def __repr__(self):
        out_dict = self.__dict__
        out_dict['company_details'] = self.company_details.__dict__
        out_str = json.dumps(out_dict, sort_keys=True, indent=4)
        return out_str