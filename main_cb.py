import os
import logging, logging.handlers
import time
import cbscraper.common
import cbscraper.company
import cbscraper.person

#GLOBALS
rescrape = True
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
def scrapePersons(company_data, key):
    company_cb_id = company_data['company_id_cb']
    company_vico_id = company_data['company_id_vico']
    p_list = company_data[key]

    if not p_list:
        logging.warning("List "+key+" is empty for "+company_cb_id)

    for p in p_list:
        person_id = cbscraper.person.getPersonIdFromLink(p[1])
        person_data = {
            "id": person_id,
            "overview": "./data/person/html/" + person_id + ".html",
            "investment_html": "./data/person/html/" + person_id + "_investments.html",
            "json": "./data/person/json/" + person_id + ".json",
            "rescrape": rescrape,
            'company_id_cb': company_cb_id,
            'company_id_vico': company_vico_id,
            'type': key  # allow to distinguish among "team", "advisors" and "past_people"
        }
        person_res = cbscraper.person.scrapePerson(person_data)

# MAIN
def main():
    logger = logging.getLogger("main")
    buildDirs()

    # Scrape company

    import pandas

    frame = pandas.read_excel(excel_file, index_col=None, header=0, sheetname=excel_sheet)

    #VICO->Crunchbase file
    frame = frame[[excel_col_cb, excel_col_vico]]  # get only interesting columns
    frame = frame.loc[frame[excel_col_cb] == frame[excel_col_cb]]  # remove NaNs

    # DEBUG
    # frame = pandas.DataFrame({'CB_ID':['actility'],'CompanyID':['VICO_CIAO']})

    counter = 1  # keep count of the current firm
    ids_len = frame.shape[0] #get row number

    for index, row in frame.iterrows():

        company_vico_id = row[excel_col_vico]
        company_cb_id = row[excel_col_cb].replace("/organization/","")

        percent = round((counter / ids_len) * 100, 2)
        logger.info("Company: " + company_cb_id + " (" + str(counter) + "/" + str(ids_len) + " - " + str(percent) + "%)")
        counter += 1

        org_data = {
            "cb_id": company_cb_id,
            "vico_id": company_vico_id,
            "overview_html": "./data/company/html/" + company_cb_id + "_overview.html",
            "advisors_html": "./data/company/html/" + company_cb_id + "_board.html",
            "people_html": "./data/company/html/" + company_cb_id + "_people.html",
            "past_people_html": "./data/company/html/" + company_cb_id + "_past_people.html",
            "json": "./data/company/json/" + company_cb_id + ".json",
            "rescrape": rescrape,
        }

        company_data = cbscraper.company.scrapeOrganization(org_data)

        # Scrape persons of the company

        if (company_data is not False):
            logger.info("Scraping persons")
            scrapePersons(company_data, 'people')

            logger.info("Scraping advisors")
            scrapePersons(company_data, 'advisors')

            logger.info("Scraping past_people")
            scrapePersons(company_data, 'past_people')
        else:
            logger.error("No company_data")

    logger.info("ENDED!")


if __name__ == "__main__":

    FORMAT = "%(asctime)s - %(levelname)-7s - [%(module)s:%(lineno)d:%(funcName)s] %(message)s"
    fmt = logging.Formatter(FORMAT, datefmt='%H:%M:%S')

    #console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)

    #add file log
    handler = logging.handlers.RotatingFileHandler('cbscraper.log', maxBytes=1024000, backupCount=5)
    handler.setFormatter(fmt)
    logging.getLogger().addHandler(handler)

    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Starting at: "+time.strftime("%Y-%m-%d"))
    main()
