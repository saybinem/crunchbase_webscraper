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
        origin_url = "./data/company/html/"+company_name+"_people.html"
    
    if(key=='advisors'):    
        origin_url = "./data/company/html/"+company_name+"_board.html"
        
    for p in company_data[key]:
        person_id = cbscraper.person.getPersonIdFromLink(p[1])
        person_data = {
            "id" : person_id,
            "overview" : "./data/person/html/"+person_id+".html",
            "json" : "./data/person/json/"+person_id+".json",
            "cookie" : cookie_data,
            "origin_url" : origin_url,
            "rescrape" : True
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

company_name = "aicuris"

org_data = {
    "name" : "aicuris",
    "overview_html" : "./data/company/html/"+company_name+"_overview.html",
    "board_html" : "./data/company/html/"+company_name+"_board.html",
    "people_html" : "./data/company/html/"+company_name+"_people.html",
    "json" : "./data/company/json/"+company_name+".json",
    "cookie" : cookie_data,
    "rescrape" : True
    }

company_data = cbscraper.company.scrapeOrganization(org_data)

# Scrape persons of the company
    
if(company_data is not False):
    
    print("[main] Scraping persons")
    scrapePersons(company_data, 'people', cookie_data)
    
    print("[main] Scraping advisors")  
    scrapePersons(company_data, 'advisors', cookie_data)

print("END!")