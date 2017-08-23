import os

from cbscraper import GenericWebScraper
import json
from cbscraper import global_vars
import copy

#Total Equity Funding
class CBCompanyOverviewStatsTEF():
    def __init__(self):
        super().__init__()
        self.funding_amount = str()
        self.funding_rounds = str()
        self.funding_investors = str()

class CBCompanyOverviewStatsIPO():
    def __init__(self):
        super().__init__()
        self.fate = str()
        self.fate_link = str()
        self.date = str()
        self.ticker = str()

class CBCompanyOverviewStatsAcqusitions():
    def __init__(self):
        super().__init__()
        self.num = -1

class CBCompanyOverviewStats():
    def __init__(self):
        super().__init__()
        self.acquisitions = CBCompanyOverviewStatsAcqusitions()
        self.ipo = CBCompanyOverviewStatsIPO()
        self.status = ''
        self.tef = CBCompanyOverviewStatsTEF()
        self.mrf = str() #Most Recent Funding

class CBCompanyOverviewSocial():
    def __init__(self):
        super().__init__()
        self.twitter = ''
        self.linkedin = ''

class CBCompanyOverview():
    def __init__(self):
        super().__init__()
        self.social = CBCompanyOverviewSocial()
        self.headquarters = ''
        self.description = ''
        self.categories = list()
        self.website = ''
        self.stats = CBCompanyOverviewStats()

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

class CBCompanyData():
    def __init__(self):
        super().__init__()
        self.company_id_vico = str()
        self.company_id_cb = str()
        self.name = str() #company name
        self.completion_perc = float()
        self.overview = CBCompanyOverview()
        self.details = CBCompanyDetails()
        self.people = list()
        self.advisors = list()
        self.past_people = list()
        self.error = str()
        self.founders = list() #founders list are part of overview, but are here for convienece reason in scraping persons

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
        out_file = os.path.join(global_vars.company_json_dir, company_id_cb+".json")
        return out_file

    def __getstate__(self):
        odict = self.__dict__
        del odict['completion_perc']
        return odict