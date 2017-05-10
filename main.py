import cbscraper.common
import cbscraper.company
import cbscraper.person
import os

def buildDirs():
    os.makedirs("./data/person/html",exist_ok=True)
    os.makedirs("./data/person/json",exist_ok=True)
    os.makedirs("./data/company/html",exist_ok=True)
    os.makedirs("./data/company/json",exist_ok=True)
    
def scrapePersons(company_data, key, cookie_data):
    company_id = company_data['id']
    
    if(key=='people'):
        origin_url = "www.crunchbase.com/company/"+company_name+"/people"
    
    if(key=='advisors'):    
        origin_url = "www.crunchbase.com/company/"+company_name+"/advisors"
        
    for p in company_data[key]:
        person_id = cbscraper.person.getPersonIdFromLink(p[1])
        person_data = {
            "id" : person_id,
            "overview" : "./data/person/html/"+person_id+".html",
            "json" : "./data/person/json/"+person_id+".json",
            "cookie" : cookie_data,
            "origin_url" : origin_url,
            "rescrape" : False
            }
        person_res = cbscraper.person.scrapePerson(person_data)
        if person_res is False:
            print("Exiting...")
            exit()
        
#MAIN
cbscraper.common.myRequest.counter = 0
buildDirs()

with open("cookie.txt") as cookie_file:
    cookie_data = cookie_file.read()
    
# Scrape company

import pandas
frame = pandas.read_excel("C:/data/tesi/pilot_project/vico_sub2.xlsx", index_col=None, header=0, sheetname="CB_HC")
ids = [str(x) for x in frame['CB_ID'] if x==x] #if x==x will remove the NaNs. A NaN is not equal to itself

for company_name in ids:
    
    print("[main] Company: "+company_name)
    
    org_data = {
        "name" : company_name,
        "overview_html" : "./data/company/html/"+company_name+"_overview.html",
        "board_html" : "./data/company/html/"+company_name+"_board.html",
        "people_html" : "./data/company/html/"+company_name+"_people.html",
        "json" : "./data/company/json/"+company_name+".json",
        "cookie" : cookie_data,
        "rescrape" : False
        }
    
    company_data = cbscraper.company.scrapeOrganization(org_data)
    
    # Scrape persons of the company
        
    if(company_data is not False):
        
        print("[main] Scraping persons")
        scrapePersons(company_data, 'people', cookie_data)
        
        print("[main] Scraping advisors")  
        scrapePersons(company_data, 'advisors', cookie_data)

print("END!")