#GLOBALS
remove_existing_json = True
rescrape = True
go_on = True #scrape unscraped companies

excel_file = r"C:\data\tesi\VICO\ID Crunchbase_ID VICO.xlsx"
vico_file = r"C:\data\tesi\VICO\VICO 4.0_REV_geocoded.csv"

excel_sheet = 'Firm'
excel_col_cb = 'CB'
excel_col_vico = 'VICO'

company_json_dir = "./data/company/json_true"
company_html_dir = './data/company/html'
company_screens_dir = './data/company/screenshots'

person_json_dir = "./data/person/json_true"
person_html_dir = './data/person/html'
person_screens_dir = './data/person/screenshots'

usepickle = False

already_scraped = list() #person ids that have already been scraped