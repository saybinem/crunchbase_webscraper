import os
import logging, logging.handlers
import time
import cbscraper.company
import cbscraper.person
from multiprocessing import Pool
import pandas
import shutil
import global_vars
import sys

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

# MAIN
def main():

    if global_vars.remove_existing_json:

        if os.path.isdir(global_vars.company_json_dir):
            logging.info("Remove company JSON directory '" + global_vars.company_json_dir + "'")
            shutil.rmtree(global_vars.company_json_dir)

        if os.path.isdir(global_vars.person_json_dir):
            logging.info("Remove person JSON directory '" + global_vars.person_json_dir + "'")
            shutil.rmtree(global_vars.person_json_dir)

    buildDirs()

    # VICO DB
    vico_frame = pandas.read_hdf(global_vars.vico_file)
    valid_vico_ids = list(vico_frame.index)

    # Get list of companies
    vico_cb_map = pandas.read_excel(global_vars.excel_file, index_col=global_vars.excel_col_vico, header=0, sheetname=global_vars.excel_sheet)

    #Count companies which are in the map but not in the vico db
    vico_frame_indexes = set(vico_frame.index)
    vico_cb_map_indexes = set(vico_cb_map.index)

    # Companies which are in the map but not in VICO
    not_vicoed_ids = vico_cb_map_indexes - vico_frame_indexes
    writeListToFile("not_vicoed_ids.txt", not_vicoed_ids)

    #Companies which are in VICO but do not have in the map
    writeListToFile("vico_frame_index.txt", vico_frame_indexes)
    writeListToFile("vico_cbmap_index.txt", vico_cb_map_indexes)

    not_mapped_ids = vico_frame_indexes - vico_cb_map_indexes
    writeListToFile("not_mapped_ids.txt", not_mapped_ids)

    if not_mapped_ids != set():
        logging.critical("The following " + str(len(not_mapped_ids)) + " companies are in VICO db but not in the map")
        logging.critical(str(not_mapped_ids))
        #sys.exit(0)

    # Build job list
    logging.info("Build job list")
    counter = 1  # keep count of the current firm
    ids_len = vico_cb_map.shape[0] #get row number
    jobs_list = list()
    not_found = set() #count companies not found in VICO db
    already_in_job = set()
    duplicates = list()

    #DataFrame.iterrows()[source]
    #Iterate over DataFrame rows as (index, Series) pairs.

    #vico_cb_map = pandas.DataFrame({'CB':pandas.Series(['/organization/crowdcube'],index=['VICO2058'])})
    #vico_cb_map = vico_cb_map[vico_cb_map.CB == '/organization/crowdcube']

    for index, row in vico_cb_map.iterrows():

        company_id_vico = index

        company_id_cb = row[global_vars.excel_col_cb].replace("/organization/","")

        # Check if the ID is in the VICO DB
        if not company_id_vico in valid_vico_ids:
            #logging.critical(company_vico_id + " (" + company_cb_id + ") is not in VICO db. Skipping")
            not_found.add(company_id_vico)
            continue
            #sys.exit(0)

        # Check if we already processed this company
        if company_id_vico in already_in_job:
            duplicates.append(company_id_vico)
            continue
        already_in_job.add(company_id_vico)

        completion_perc = round((counter / ids_len) * 100, 2)
        counter += 1

        org_data = {
            "company_id_cb" : company_id_cb,
            "company_id_vico" : company_id_vico,
            "json" : os.path.join(global_vars.company_json_dir, company_id_cb + ".json"),
            "completion_perc" : completion_perc
        }

        jobs_list.append(org_data)

    logging.info("Firms not found in VICO = " + str(not_found))
    not_found_count = len(not_found)
    not_found_set_count = len(set(not_found))
    job_count = len(jobs_list)
    mapped_firms_count = len(set(vico_cb_map.index))
    diff = mapped_firms_count - job_count
    logging.info("not_found_count=" + str(not_found_count)
                 + ", not_found_set_count=" + str(not_found_set_count)
                 + ", job_count=" + str(job_count)
                 + ", mapped_firms_count=" + str(mapped_firms_count)
                 + ", diff=" + str(diff))

    logging.info("Duplicates: "+str(duplicates))
    writeListToFile("duplicate_mapped.txt", duplicates)

    # Assert that we have skipped all companies which do not have a correspondence on VICO
    #assert(set(not_found) == not_vicoed_ids)

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
