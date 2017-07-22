#GLOBALS
remove_existing_json = False
rescrape = False
go_on = False #scrape unscraped companies

excel_file = r"C:\data\tesi\VICO\ID Crunchbase_ID VICO.xlsx"
vico_file = r"C:\data\tesi\VICO\VICO 4.0_REV_geocoded.hdf5"

excel_sheet = 'Firm'
excel_col_cb = 'CB'
excel_col_vico = 'VICO'
company_json_dir = "./data/company/json"
person_json_dir = "./data/person/json"