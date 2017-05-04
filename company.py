import common
import os
import re

#Scrape a company
def scrapeOrganization(company_name):
    
    print("Scraping company people "+company_name)
    html_file_people = "./company/html/"+company_name+"_people.html"
    html_file_advisors = "./company/html/"+company_name+"_board.html"
    json_file = "./company/json/"+company_name+".json"
    
    people_url = 'https://www.crunchbase.com/organization/'+company_name+'/people'
    print("Getting people from: "+people_url)
    soup_people = common.getPageSoup(people_url, html_file_people)
    if(soup_people is False):
        return False
    
    soup_advisors = common.getPageSoup('https://www.crunchbase.com/organization/'+company_name+'/advisors', html_file_advisors)
    if(soup_advisors is False):
        return False
     
    #Get people
    people = list()
    for div_people in soup_people.find_all('div',class_='people'):
        for info_block in div_people.find_all('div',class_='info-block'):
            h4 = info_block.find('h4')
            a = h4.a   
            name = a.get('data-name')
            link = a.get('href')
            role = info_block.find('h5').text
            people.append([name, link, role])
                
    #Get main advisors + more advisors
    advisors = list()
    for div_advisors in soup_advisors.find_all('div',class_='advisors'):
        for info_block in div_advisors.find_all('div',class_='info-block'):
            name = info_block.h4.text
            primary_role = info_block.h5.text #the primary role of this person (may not be related to the company at hand)
            role_in_bod = info_block.h6.text #his role in our company's BoD
            advisors.append([name, primary_role, role_in_bod])
                
    #Save to file
    company_data = {'people':people, 'advisors': advisors}
    with open(json_file,'w') as fileh:
        fileh.write(common.jsonPrettyDict(company_data))
    return company_data