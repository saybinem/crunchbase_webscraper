import GenericScraper
import logging
import global_vars
import FrozenClass

class CBPersonDataOverviewSocial(FrozenClass.StringHolder):
    valid_keys = {'facebook', 'linkedin', 'twitter'}

class CBPersonDataOverviewPrimaryRole(FrozenClass.StringHolder):
    valid_keys = {'role', 'firm'}

class CBPersonDataOverview(FrozenClass.RFrozenClass):

    def __init__(self, in_dict = None):
        super().__init__()
        if not in_dict:
            self.primary_role = CBPersonDataOverviewPrimaryRole()
            self.social = CBPersonDataOverviewSocial()
            self.born = ''
            self.gender = ''
            self.location = ''
        else:
            del in_dict['_RFrozenClass__isfrozen']
            valid_keys = {'primary_role', 'social', 'born', 'gender', 'location'}
            assert (set(in_dict.keys()) == valid_keys)
            assert (type(in_dict['born'] == str))
            assert (type(in_dict['gender'] == str))
            assert (type(in_dict['location'] == str))
            self.__dict__ = in_dict
            pr = CBPersonDataOverviewPrimaryRole(in_dict['primary_role'])
            self.primary_role = pr
            soc = CBPersonDataOverviewSocial(in_dict['social'])
            self.social = soc
        self._freeze()

    def serialize(self):
        out_dict = self.__dict__
        out_dict['primary_role'] = self.primary_role.serialize()
        out_dict['social'] = self.social.serialize()
        return out_dict

class CBPersonData(FrozenClass.RFrozenClass):

    def __init__(self, infile=None):
        super().__init__()
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
        out_dict = self.__dict__
        out_dict['overview'] = self.overview.serialize()
        GenericScraper.saveDictToJsonFile(out_dict, outfile)

    def load(self, infile):
        in_dict = GenericScraper.readJSONFile(infile)
        ov = CBPersonDataOverview(in_dict['overview'])
        in_dict['overview'] = ov
        self.__dict__ = in_dict

    def hasLILink(self):
        return self.overview.social.linkedin == ''

    def getLILink(self):
        return self.overview.social.linkedin
