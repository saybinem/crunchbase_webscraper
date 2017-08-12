import os

from cbscraper import GenericWebScraper
from cbscraper import CBCompanyDetails
import json
from cbscraper import global_vars
import copy

class CBCompanyData():
    def __init__(self):
        super().__init__()
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
        out_dict = copy.copy(self.__dict__)
        if "company_details" in out_dict:
            out_dict['company_details'] = copy.copy(self.company_details.__dict__)
        out_str = json.dumps(out_dict, sort_keys=True, indent=4)
        return out_str

    @staticmethod
    def genPathFromID(company_id_cb):
        partial_out_file = os.path.join(global_vars.company_json_dir, company_id_cb)
        out_file = GenericWebScraper.genFullFilename(partial_out_file)
        return out_file