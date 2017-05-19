import cbscraper.common
import cbscraper.company
import cbscraper.person
import os

#make data dirs if they do not exists
def buildDirs():
    os.makedirs("./data/person/html",exist_ok=True)
    os.makedirs("./data/person/json",exist_ok=True)
    os.makedirs("./data/company/html",exist_ok=True)
    os.makedirs("./data/company/json",exist_ok=True)
    
#Give a company, scrape the team and the advisors
#company_data = a dict returned by cbscraper.company.scrapeOrganization()
#key = the dictionary key that contains the list of lists of company persons
def scrapePersons(company_data, key):
    
    company_cb_id = company_data['company_id_cb']
    company_vico_id = company_data['company_id_vico']
    
    for p in company_data[key]:
        person_id = cbscraper.person.getPersonIdFromLink(p[1])
        person_data = {
            "id" : person_id,
            "overview" : "./data/person/html/"+person_id+".html",
            "json" : "./data/person/json/"+person_id+".json",
            "rescrape" : True,
            'company_id_cb': company_cb_id,
            'company_id_vico' : company_vico_id
            }
        person_res = cbscraper.person.scrapePerson(person_data)
        
#MAIN
cbscraper.common.myRequest.counter = 0
buildDirs()

# Scrape company

import pandas
frame = pandas.read_excel("C:/data/tesi/pilot_project/vico_sub2.xlsx", index_col=None, header=0, sheetname="CB_HC")

frame = frame[['CB_ID', 'CompanyID']]

#print(str(frame))

frame = frame.loc[frame['CB_ID'] == frame['CB_ID']] #remove NaNs
frame.reset_index(inplace=True, drop=True)

#print(str(frame))
#exit()

#ids = ['cambridge-broadband-networks']

counter = 1
ids_len = frame.shape[0]

for index, row in frame.iterrows():
    
    company_vico_id = row['CompanyID'] 
    company_cb_id = row['CB_ID']
    
    percent = round((counter / ids_len) * 100,2)
    print("[main] Company: " + company_cb_id + " ("+str(counter)+"/"+str(ids_len)+" - "+str(percent)+"%)")
    counter += 1
        
    org_data = {
        "cb_id" : company_cb_id,
        "vico_id" : company_vico_id,
        "overview_html" : "./data/company/html/"+company_cb_id+"_overview.html",
        "board_html" : "./data/company/html/"+company_cb_id+"_board.html",
        "people_html" : "./data/company/html/"+company_cb_id+"_people.html",
        "json" : "./data/company/json/"+company_cb_id+".json",
        "rescrape" : True,
        }
    
    company_data = cbscraper.company.scrapeOrganization(org_data)
    
    # Scrape persons of the company
        
    if(company_data is not False):
        
        print("[main] Scraping persons")
        scrapePersons(company_data, 'people')
            
        print("[main] Scraping advisors")  
        scrapePersons(company_data, 'advisors')

print("END!")