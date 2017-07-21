import os
import logging, logging.handlers
import time
import cbscraper.company
import cbscraper.person
from multiprocessing import Pool
import pandas
import shutil
import global_vars

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

    if global_vars.remove_existing_json:

        company_json_dir = "./data/company/json"
        person_json_dir = "./data/person/json"

        if os.path.isdir(company_json_dir):
            logging.info("Remove company JSON directory '" + company_json_dir + "'")
            shutil.rmtree(company_json_dir)

        if os.path.isdir(person_json_dir):
            logging.info("Remove person JSON directory '" + person_json_dir + "'")
            shutil.rmtree(person_json_dir)

    buildDirs()

    # Get list of companies
    frame = pandas.read_excel(global_vars.excel_file, index_col=None, header=0, sheetname=global_vars.excel_sheet)
    frame = frame[[global_vars.excel_col_cb, global_vars.excel_col_vico]]  # get only interesting columns
    frame = frame.loc[frame[global_vars.excel_col_cb] == frame[global_vars.excel_col_cb]]  # remove NaNs

    counter = 1  # keep count of the current firm
    ids_len = frame.shape[0] #get row number

    jobs_list = list()

    # Build job list
    logging.info("Build job list")
    for index, row in frame.iterrows():

        company_vico_id = row[global_vars.excel_col_vico]
        company_cb_id = row[global_vars.excel_col_cb].replace("/organization/","")
        completion_perc = round((counter / ids_len) * 100, 2)
        counter += 1

        org_data = {
            "cb_id": company_cb_id,
            "vico_id": company_vico_id,
            "json": "./data/company/json/" + company_cb_id + ".json",
            "completion_perc" : completion_perc
        }

        jobs_list.append(org_data)

    # Run job list
    logging.info("Running job list")

    #with Pool(10) as p:
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
