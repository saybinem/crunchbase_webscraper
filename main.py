import cbscraper.common
import cbscraper.company
import cbscraper.person
import os

def buildDirs():
    os.makedirs("./data/person/html",exist_ok=True)
    os.makedirs("./data/person/json",exist_ok=True)
    os.makedirs("./data/company/html",exist_ok=True)
    os.makedirs("./data/company/json",exist_ok=True)
    
def myScrapeSinglePerson(person_id, origin_url):
    person_html_files = {"overview" : "./data/person/html/"+person_id+".html"}
    person_json_file = "./data/person/json/"+person_id+".json"
    person_data = cbscraper.person.scrapePerson(person_id, person_html_files, person_json_file, origin_url, False)
    return person_data
        
#MAIN

cbscraper.common.myRequest.counter = 0

buildDirs()

# Scrape company
company_name = "ip-access"

company_html_files = {
        "overview" : "./data/company/html/"+company_name+"_overview.html",
        "board" : "./data/company/html/"+company_name+"_board.html",
        "people" : "./data/company/html/"+company_name+"_people.html"
        }
company_json_file = "./data/company/json/"+company_name+".json"

company_data = cbscraper.company.scrapeOrganization(company_name, company_html_files, company_json_file, False)

# Scrape persons of the company
people_url = 'https://www.crunchbase.com/organization/'+company_name+'/people'
advisor_url = 'https://www.crunchbase.com/organization/'+company_name+'/advisors'
    
if(company_data is not False):
    
    print("[main] Scraping persons")
    for p in company_data['people']:
        if myScrapeSinglePerson(cbscraper.person.getPersonIdFromLink(p[1]), people_url) is False:
            print("Exiting...")
            exit()
    
    print("[main] Scraping advisors")  
    for p in company_data['advisors']:
        if myScrapeSinglePerson(cbscraper.person.getPersonIdFromLink(p[1]), advisor_url) is False:
            print("Exiting...")
            exit()

print("END!")