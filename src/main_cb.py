import logging
import logging.handlers
import os
import shutil
import time
import sys

import cbscraper.company
import cbscraper.person
import jsonpickle
import simplejson
import pandas
from cbscraper.CBCompanyData import CBCompanyData
from cbscraper import global_vars


# make data dirs if they do not exists
def buildDirs():
    os.makedirs("./data/person/html", exist_ok=True)
    os.makedirs("./data/person/json", exist_ok=True)
    os.makedirs("./data/person/screenshots", exist_ok=True)
    os.makedirs("./data/company/html", exist_ok=True)
    os.makedirs("./data/company/json", exist_ok=True)
    os.makedirs("./data/company/screenshots", exist_ok=True)


def writeListToFile(file, list):
    fileh = open(file, "w", encoding="utf-8")
    for company in list:
        fileh.write(str(company) + "\n")
    fileh.close()


def removeDirs():
    # Remove existing JSON files
    if global_vars.remove_existing_json:
        if os.path.isdir(global_vars.company_json_dir):
            logging.info("Remove company JSON directory '" + global_vars.company_json_dir + "'")
            shutil.rmtree(global_vars.company_json_dir)

        if os.path.isdir(global_vars.person_json_dir):
            logging.info("Remove person JSON directory '" + global_vars.person_json_dir + "'")
            shutil.rmtree(global_vars.person_json_dir)


# MAIN
def main():
    removeDirs()
    buildDirs()
    jsonpickle.set_encoder_options('json', indent=4)

    # VICO DB
    logging.info("Reading VICO db")
    vico_frame = pandas.read_csv(global_vars.vico_file, index_col='CompanyID', header=0, low_memory=False)
    valid_vico_ids = list(vico_frame.index)

    # Get list of companies
    logging.info("Reading map")
    vico_to_cb_map = pandas.read_excel(global_vars.excel_file, index_col=global_vars.excel_col_vico, header=0,
                                       sheetname=global_vars.excel_sheet)

    # Build job list
    logging.info("Build job list")
    counter = 1  # keep count of the current firm
    ids_len = vico_to_cb_map.shape[0]  # get row number
    jobs_list = list()
    not_found = set()  # companies in the map but NOT in the VICO db
    already_in_job = set()  # list of companies which we have put in job
    duplicates = list()  # list of duplicates companies

    for company_id_vico, row in vico_to_cb_map.iterrows():

        company_id_cb = row[global_vars.excel_col_cb].replace("/organization/", "")

        # Check if the ID is in the VICO DB
        if not company_id_vico in valid_vico_ids:
            #logging.debug(company_id_vico + " (" + company_id_vico + ") is not in VICO db. Skipping")
            not_found.add(company_id_vico)
            continue

        # Check if we already processed this company
        if company_id_vico in already_in_job:
            duplicates.append(company_id_vico)
            continue
        already_in_job.add(company_id_vico)

        # Calculate percentage completion
        completion_perc = round((counter / ids_len) * 100, 2)
        counter += 1
        company_data = CBCompanyData()
        company_data.company_id_cb = company_id_cb
        company_data.company_id_vico = company_id_vico
        company_data.completion_perc = completion_perc
        jobs_list.append(company_data)

    # Duplicates count
    logging.info("Found " + str(len(duplicates)) + " duplicates")

    # Run job list
    logging.info("Running job list")

    # with Pool(10) as p:
    #    p.map(cbscraper.company.scrapeOrgAndPeople, jobs_list)

    for job in jobs_list:
        cbscraper.company.scrapeOrgAndPeople(job)

    logging.info("ENDED!")

def setLoggers():
    log_format_str = "[%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(funcName)s] %(message)s"
    fmt = logging.Formatter(log_format_str, datefmt='%H:%M:%S')

    # console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)

    # log file handler
    # handler = logging.handlers.RotatingFileHandler('cbscraper.log', maxBytes=1024000, backupCount=5)
    # handler.setFormatter(fmt)
    # logging.getLogger().addHandler(handler)

    # root logger
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Starting at: " + time.strftime("%Y-%m-%d"))

if __name__ == "__main__":

    setLoggers()

    # SET VARS
    jsonpickle.set_preferred_backend('simplejson')
    jsonpickle.set_encoder_options('simplejson', indent=4)

    logging.info("Recursion limit: "+str(sys.getrecursionlimit()))
    sys.setrecursionlimit(30000)
    logging.info("Recursion limit: " + str(sys.getrecursionlimit()))
    #sys.exit(0)

    #MAIN
    main()
