import os
import logging, logging.handlers
import time
import cbscraper.common
import cbscraper.company
import cbscraper.person

#GLOBALS
rescrape = False
excel_file = r"C:\data\tesi\VICO\ID Crunchbase_ID VICO.xlsx"
excel_sheet = 'Firm'
excel_col_cb = 'CB'
excel_col_vico = 'VICO'

# make data dirs if they do not exists
def buildDirs():
    os.makedirs("./data/person/html", exist_ok=True)
    os.makedirs("./data/person/json", exist_ok=True)
    os.makedirs("./data/company/html", exist_ok=True)
    os.makedirs("./data/company/json", exist_ok=True)


# Give a company, scrape current people, past people and advisors
# company_data = a dict returned by cbscraper.company.scrapeOrganization()
# key = the dictionary key that contains the list of lists of company persons
def scrapePersons(company_data, key, company_percent):
    company_cb_id = company_data['company_id_cb']
    company_vico_id = company_data['company_id_vico']
    p_list = company_data[key]

    if not p_list:
        logging.warning("List "+key+" is empty for "+company_cb_id)

    for p in p_list:
        person_id = cbscraper.person.getPersonIdFromLink(p[1])
        person_data = {
            "company_percent" : company_percent,
            "id": person_id,
            "json": "./data/person/json/" + person_id + ".json",
            "rescrape": rescrape,
            'company_id_cb': company_cb_id,
            'company_id_vico': company_vico_id,
            'type': key  # allow to distinguish among "team", "advisors" and "past_people"
        }
        cbscraper.person.scrapePerson(person_data)

# MAIN
def main():
    buildDirs()

    #DEBUG
    if False:
        org_data = {
            "cb_id": "facebook",
            "vico_id": "NONEXIST",
            "json": "./data/company/json/facebook.json",
            "rescrape": True,
        }
        company_data = cbscraper.company.scrapeOrganization(org_data)
        exit()

    # Scrape company

    import pandas

    frame = pandas.read_excel(excel_file, index_col=None, header=0, sheetname=excel_sheet)

    #VICO->Crunchbase file
    frame = frame[[excel_col_cb, excel_col_vico]]  # get only interesting columns
    frame = frame.loc[frame[excel_col_cb] == frame[excel_col_cb]]  # remove NaNs

    counter = 1  # keep count of the current firm
    ids_len = frame.shape[0] #get row number

    for index, row in frame.iterrows():

        company_vico_id = row[excel_col_vico]
        company_cb_id = row[excel_col_cb].replace("/organization/","")

        company_percent = round((counter / ids_len) * 100, 2)
        msg = "Company: " + company_cb_id + " (" + str(counter) + "/" + str(ids_len) + " - " + str(company_percent) + "%)"
        logging.info(msg)

        counter += 1

        org_data = {
            "cb_id": company_cb_id,
            "vico_id": company_vico_id,
            "json": "./data/company/json/" + company_cb_id + ".json",
            "rescrape": rescrape,
        }

        company_data = cbscraper.company.scrapeOrganization(org_data)

        # Scrape persons of the company

        if (company_data is not False):
            logging.info("Scraping persons")
            scrapePersons(company_data, 'people', company_percent)

            logging.info("Scraping advisors")
            scrapePersons(company_data, 'advisors', company_percent)

            logging.info("Scraping past_people")
            scrapePersons(company_data, 'past_people', company_percent)
        else:
            logging.error("scrapeOrganization() returned False. This means there is no company_data")

    logging.info("ENDED!")


if __name__ == "__main__":

    format_str = "%(asctime)s - %(levelname)-7s - [%(filename)s : %(lineno)d : %(funcName)s] %(message)s"
    fmt = logging.Formatter(format_str, datefmt='%H:%M:%S')

    #console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)

    #add file log
    if False:
        handler = logging.handlers.RotatingFileHandler('cbscraper.log', maxBytes=1024000, backupCount=5)
        handler.setFormatter(fmt)
        logging.getLogger().addHandler(handler)

    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Starting at: "+time.strftime("%Y-%m-%d"))
    main()
