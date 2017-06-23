import os

import cbscraper.common
import cbscraper.company
import cbscraper.person


# make data dirs if they do not exists
def buildDirs():
    os.makedirs("./data/person/html", exist_ok=True)
    os.makedirs("./data/person/json", exist_ok=True)
    os.makedirs("./data/company/html", exist_ok=True)
    os.makedirs("./data/company/json", exist_ok=True)


# Give a company, scrape the team and the advisors
# company_data = a dict returned by cbscraper.company.scrapeOrganization()
# key = the dictionary key that contains the list of lists of company persons
def scrapePersons(company_data, key):
    company_cb_id = company_data['company_id_cb']
    company_vico_id = company_data['company_id_vico']

    p_list = company_data[key]

    if not p_list:
        print("[scrapePersons]List is empty")

    for p in p_list:
        person_id = cbscraper.person.getPersonIdFromLink(p[1])
        person_data = {
            "id": person_id,
            "overview": "./data/person/html/" + person_id + ".html",
            "json": "./data/person/json/" + person_id + ".json",
            "rescrape": True,
            'company_id_cb': company_cb_id,
            'company_id_vico': company_vico_id,
            'type': key  # allow to distinguish among "team", "advisors" and "past_people"
        }
        person_res = cbscraper.person.scrapePerson(person_data)


# MAIN
def main():
    buildDirs()

    # Scrape company

    import pandas
    frame = pandas.read_excel("C:/data/tesi/pilot_project/vico_sub2.xlsx", index_col=None, header=0, sheetname="CB_HC")
    frame = frame[['CB_ID', 'CompanyID']]  # get only interesting columns
    frame = frame.loc[frame['CB_ID'] == frame['CB_ID']]  # remove NaNs
    frame.reset_index(inplace=True, drop=True)  # drop index

    # DEBUG
    # frame = pandas.DataFrame({'CB_ID':['actility'],'CompanyID':['VICO_CIAO']})

    counter = 1  # keep count of the current firm
    ids_len = frame.shape[0]

    for index, row in frame.iterrows():

        company_vico_id = row['CompanyID']
        company_cb_id = row['CB_ID']

        percent = round((counter / ids_len) * 100, 2)
        print(
            "[main] Company: " + company_cb_id + " (" + str(counter) + "/" + str(ids_len) + " - " + str(percent) + "%)")
        counter += 1

        org_data = {
            "cb_id": company_cb_id,
            "vico_id": company_vico_id,
            "overview_html": "./data/company/html/" + company_cb_id + "_overview.html",
            "board_html": "./data/company/html/" + company_cb_id + "_board.html",
            "people_html": "./data/company/html/" + company_cb_id + "_people.html",
            "past_people_html": "./data/company/html/" + company_cb_id + "_past_people.html",
            "json": "./data/company/json/" + company_cb_id + ".json",
            "rescrape": True,
        }

        company_data = cbscraper.company.scrapeOrganization(org_data)

        # Scrape persons of the company

        if (company_data is not False):
            print("[main] Scraping persons")
            scrapePersons(company_data, 'people')

            print("[main] Scraping advisors")
            scrapePersons(company_data, 'advisors')

            print("[main] Scraping past_people")
            scrapePersons(company_data, 'past_people')

    print("END!")


if __name__ == "__main__":
    main()
