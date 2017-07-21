import GenericScraper
import logging
import global_vars
import FrozenClass

class CBPersonDataOverviewSocial(FrozenClass.RFrozenClass):
    def __init__(self, in_dict = None):
        if not in_dict:
            self.facebook = ''
            self.linkedin = ''
            self.twitter = ''
        else:
            assert (set(in_dict.keys()) == {'facebook', 'linkedin', 'twitter''})
            self.__dict__ = in_dict
        self._freeze()

    def serialize(self):
        return self.__dict__

class CBPersonDataOverviewPrimaryRole(FrozenClass.RFrozenClass):
    def __init__(self, in_dict = None):
        if not in_dict:
            self.role = ''
            self.firm = ''
        else:
            assert(set(in_dict.keys()) == {'role','firm'})
            self.__dict__ = in_dict
        self._freeze()

    def serialize(self):
        return self.__dict__

class CBPersonDataOverview(FrozenClass.RFrozenClass):
    def __init__(self, in_dict):
        if not in_dict:
            self.primary_role = CBPersonDataOverviewPrimaryRole()
            self.social = CBPersonDataOverviewSocial()
            self.born = ''
            self.gender = ''
            self.location = ''
        else:
            self.__dict__ = in_dict
            self.primary_role = CBPersonDataOverviewPrimaryRole(in_dict['primary_role'])
            self.social = CBPersonDataOverviewSocial(in_dict['social'])
        self._freeze()

    def serialize(self):
        self.primary_role = self.primary_role.serialize()
        self.social = self.social.serialize()
        return self.__dict__

class CBPersonData(FrozenClass.RFrozenClass):

    def __init__(self, infile=None):
        if infile is not None:
            self.load(infile)
        else:
            self.type = str()
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
        self._freeze()

    def save(self, outfile):
        overview_copy = self.overview
        self.overview = self.overview.serialize()
        GenericScraper.saveDictToJsonFile(self.__dict__, outfile)
        self.overview = overview_copy #restore overview object

    def load(self, infile):
        in_dict = GenericScraper.readJSONFile(infile)
        in_dict['overview'] = CBPersonDataOverview(in_dict['overview'])
        self.__dict__ = in_dict

    def hasLILink(self):
        if not 'social' in self.overview:
            return False
        if not 'linkedin' in self.overview['social']:
            return False
        return True

    def getLILink(self):
        if not 'social' in self.overview:
            return ''
        if not 'linkedin' in self.overview['social']:
            return ''
        return self.overview['social']['linkedin']
