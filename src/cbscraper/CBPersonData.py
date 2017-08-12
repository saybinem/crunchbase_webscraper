
from cbscraper import GenericWebScraper
from enum import Enum, unique
import os
import logging
from cbscraper import global_vars
import pprint
import json

@unique
class EPersonType(str, Enum):
    PEOPLE = 'people'
    ADVISORS = 'advisors'
    PAST_PEOPLE = 'past_people'
    FOUNDERS = 'founders'


class CBPersonDataOverviewSocial():
    def __init__(self):
        super().__init__()
        self.facebook = str()
        self.linkedin = str()
        self.twitter = str()

class CBPersonDataOverviewPrimaryRole():
    def __init(self):
        super().__init__()
        self.role=''
        self.firm=''

class CBPersonDataOverview():
    def __init__(self):
        super().__init__()
        self.primary_role = CBPersonDataOverviewPrimaryRole()
        self.social = CBPersonDataOverviewSocial()
        self.born = ''
        self.gender = ''
        self.location = ''
        #self._freeze()

class CBPersonData(object):
    def __init__(self):
        super().__init__()
        self.person_id_cb = str()
        self.company_id_cb = str()
        self.company_id_vico = str()
        self.name = str()
        self.person_details = str()
        self.error = str()
        self.stat_code = str()
        self.overview = CBPersonDataOverview()
        self.current_jobs = list()
        self.past_jobs = list()
        self.advisory_roles = list()
        self.education = list()
        self.investments = list()
        # person type list
        self.is_founder = False
        self.is_current_people = False
        self.is_past = False
        self.is_adv = False
        #self._freeze()

    def setType(self, type):
        if type==EPersonType.FOUNDERS:
            self.is_founder = True
        elif type==EPersonType.PAST_PEOPLE:
            self.is_past = True
        elif type==EPersonType.ADVISORS:
            self.is_adv = True
        elif type==EPersonType.PEOPLE:
            self.is_current_people = True
        else:
            logging.critical(str(type)+" not in EPersonType")
            assert(False)

    def save(self, outfile, overwrite=False):
        assert(outfile != '')
        if not overwrite:
            assert(not os.path.isfile(outfile))
        GenericWebScraper.saveJSON(self, outfile)

    def hasLILink(self):
        return self.overview.social.linkedin == ''

    def getLILink(self):
        return self.overview.social.linkedin

    @staticmethod
    def genPathFromId(person_id_cb):
        partial = os.path.join(global_vars.person_json_dir, person_id_cb)
        person_out_file = GenericWebScraper.genFullFilename(partial)
        return person_out_file
        
    def __repr__(self):
        out = self.__dict__.copy()
        out['overview'] = self.overview.__dict__.copy()
        out['overview']['primary_role'] = self.overview.primary_role.__dict__.copy()
        out['overview']['social'] = self.overview.social.__dict__.copy()
        return json.dumps(out, indent=4)