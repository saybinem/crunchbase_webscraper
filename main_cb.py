import os
import logging, logging.handlers
import time
import cbscraper.company
import cbscraper.person
from multiprocessing import Pool
import pandas

#GLOBALS
rescrape = True
go_on = False #scrape unscraped companies
excel_file = r"C:\data\tesi\VICO\ID Crunchbase_ID VICO.xlsx"
excel_sheet = 'Firm'
excel_col_cb = 'CB'
excel_col_vico = 'VICO'

# make data dirs if they do not exists
def buildDirs():
    os.makedirs("./data/person/html", exist_ok=True)
    os.makedirs("./data/person/json", exist_ok=True)
    os.makedirs("./data/person/screenshots", exist_ok=True)
    os.makedirs("./data/company/html", exist_ok=True)
    os.makedirs("./data/company/json", exist_ok=True)
    os.makedirs("./data/company/screenshots", exist_ok=True)


# MAIN
def main():
    buildDirs()

    # Scrape company

    frame = pandas.read_excel(excel_file, index_col=None, header=0, sheetname=excel_sheet)

    #VICO->Crunchbase file
    frame = frame[[excel_col_cb, excel_col_vico]]  # get only interesting columns
    frame = frame.loc[frame[excel_col_cb] == frame[excel_col_cb]]  # remove NaNs

    counter = 1  # keep count of the current firm
    ids_len = frame.shape[0] #get row number

    #DEBUG
    #frame=pandas.DataFrame({excel_col_cb:['feedvisor'],excel_col_vico:['NONE']})

    jobs_list = list()

    # Build job list
    logging.info("Build job list")
    for index, row in frame.iterrows():

        company_vico_id = row[excel_col_vico]
        company_cb_id = row[excel_col_cb].replace("/organization/","")

        completion_perc = round((counter / ids_len) * 100, 2)

        counter += 1

        org_data = {
            "cb_id": company_cb_id,
            "vico_id": company_vico_id,
            "json": "./data/company/json/" + company_cb_id + ".json",
            "rescrape": rescrape,
            "go_on" : go_on,
            "completion_perc" : completion_perc
        }

        jobs_list.append(org_data)

    # Run job list
    logging.info("Running job list")
    #with Pool(1) as p:
    #    p.map(cbscraper.company.scrapeOrgAndPeople, jobs_list)
    for job in jobs_list:
        cbscraper.company.scrapeOrgAndPeople(job)

    logging.info("ENDED!")


if __name__ == "__main__":

    log_format_str = "[%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(funcName)s] %(message)s"
    fmt = logging.Formatter(log_format_str, datefmt='%H:%M:%S')

    #console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)

    #log file handler
    #handler = logging.handlers.RotatingFileHandler('cbscraper.log', maxBytes=1024000, backupCount=5)
    #handler.setFormatter(fmt)
    #logging.getLogger().addHandler(handler)

    #root logger
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Starting at: "+time.strftime("%Y-%m-%d"))
    main()
