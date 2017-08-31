#GLOBALS
import logging

remove_existing_json = False
new_companies = 0 # scrape unscraped companies

cb_vico_map_file = r"C:\data\tesi\VICO\ID Crunchbase_ID VICO.xlsx"
vico_file = r"C:\data\tesi\VICO\VICO 4.0_REV_geocoded.csv"

excel_sheet = 'Firm'
excel_col_cb = 'CB'
excel_col_vico = 'VICO'

company_json_dir = "./tagged_data/company/json"
company_html_dir = './tagged_data/company/html'
company_screens_dir = './tagged_data/company/screenshots'

person_json_dir = "./tagged_data/person/json"
person_html_dir = './tagged_data/person/html'
person_screens_dir = './tagged_data/person/screenshots'

console_log_level = logging.INFO

# GLOBAL TO NOT MODIFY
already_scraped = list() #person ids that have already been scraped