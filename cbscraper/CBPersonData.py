import FrozenClass
import GenericWebScraper
from enum import Enum, unique
import os
import logging

@unique
class EPersonType(str, Enum):
    PEOPLE = 'people'
    ADVISORS = 'advisors'
    PAST_PEOPLE = 'past_people'
    FOUNDERS = 'founders'


class CBPersonDataOverviewSocial(FrozenClass.StringHolder):
    valid_keys = {'facebook', 'linkedin', 'twitter'}


class CBPersonDataOverviewPrimaryRole(FrozenClass.StringHolder):
    valid_keys = {'role', 'firm'}


class CBPersonDataOverview(FrozenClass.RFrozenClass):
    def __init__(self, in_dict=None):
        super().__init__()
        if not in_dict:
            self.primary_role = CBPersonDataOverviewPrimaryRole()
            self.social = CBPersonDataOverviewSocial()
            self.born = ''
            self.gender = ''
            self.location = ''
        else:
            valid_keys = {'primary_role', 'social', 'born', 'gender', 'location'}
            assert (set(in_dict.keys()) == valid_keys)
            assert (type(in_dict['born'] == str))
            assert (type(in_dict['gender'] == str))
            assert (type(in_dict['location'] == str))
            self.setDict(in_dict)
            pr = CBPersonDataOverviewPrimaryRole(in_dict['primary_role'])
            self.primary_role = pr
            soc = CBPersonDataOverviewSocial(in_dict['social'])
            self.social = soc
        self._freeze()

    def serialize(self):
        out_dict = self.getDict()
        out_dict['primary_role'] = self.primary_role.serialize()
        out_dict['social'] = self.social.serialize()
        return out_dict


class CBPersonData(FrozenClass.RFrozenClass):
    def __init__(self, infile=None):
        super().__init__()
        if infile is not None:
            self._load(infile)
        else:
            self.json_file = str()
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
        self._freeze()

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

    def save(self, overwrite=False):
        assert(self.json_file != '')
        if not overwrite:
            assert(not os.path.isfile(self.json_file))
        out_dict = self.getDict()
        out_dict['overview'] = self.overview.serialize()
        del out_dict['json_file']
        #logging.info(GenericWebScraper.jsonPretty(self.getDict()))
        GenericWebScraper.saveJSON(out_dict, self.json_file)

    def _load(self, json_file):
        in_dict = GenericWebScraper.readJSONFile(json_file)
        ov = CBPersonDataOverview(in_dict['overview'])
        in_dict['overview'] = ov
        self.setDict(in_dict)
        self.json_file = json_file

    def hasLILink(self):
        return self.overview.social.linkedin == ''

    def getLILink(self):
        return self.overview.social.linkedin
