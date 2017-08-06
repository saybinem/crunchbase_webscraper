#GLOBALS
remove_existing_json = False
rescrape = False
go_on = True #scrape unscraped companies

excel_file = r"C:\data\tesi\VICO\ID Crunchbase_ID VICO.xlsx"
vico_file = r"C:\data\tesi\VICO\VICO 4.0_REV_geocoded.csv"

excel_sheet = 'Firm'
excel_col_cb = 'CB'
excel_col_vico = 'VICO'
company_json_dir = "./data/company/json"
person_json_dir = "./data/person/json"

already_scraped = list() #person ids that have already been scraped