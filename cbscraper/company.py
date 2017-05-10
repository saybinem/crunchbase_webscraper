import cbscraper.common
import os
import re
import json
from pprint import pprint

#Scrape a company
def scrapeOrganization(company_name, html_files, json_file, rescrape = True):
    
    if(os.path.isfile(json_file) and not rescrape):
        print("[scrapeOrganization] Organization already scraped")
        with open(json_file, 'r') as fileh:
            org_data = json.load(fileh)
        return org_data
    
    print("[scrapeOrganization] Scraping company "+company_name)
    html_file_overview = html_files['overview']
    html_file_people = html_files['people']
    html_file_advisors = html_files['board']
    
    # Get page "overview"
    overview_url = 'https://www.crunchbase.com/organization/'+company_name
    print("\tGetting company overview ("+overview_url+")")    
    soup_overview = cbscraper.common.getPageSoup(overview_url, html_file_overview, '')
    if(soup_overview is False):
        print("\tError in making overview soup")
        return False
    
    # Get page "people"
    people_url = 'https://www.crunchbase.com/organization/'+company_name+'/people'
    print("\tGetting company people ("+people_url+")")    
    soup_people = cbscraper.common.getPageSoup(people_url, html_file_people, overview_url)
    if(soup_people is False):
        print("\tError in making people soup")
        return False
    
    # Get page "advisors"
    advisor_url = 'https://www.crunchbase.com/organization/'+company_name+'/advisors'
    print("\tGetting company advisors ("+advisor_url+")")
    soup_advisors = cbscraper.common.getPageSoup(advisor_url, html_file_advisors, overview_url)
    if(soup_advisors is False):
        print("\tError while making advisory soup")
        return False
    
    #Scrape page "overview"
    overview = {}
    
    # Headquarters
    tag = soup_overview.find('dt', string='Headquarters:')
    if tag is not None:
        overview['headquarters'] = tag.find_next('dd').text
    
    # Description
    tag = soup_overview.find('dt', string='Description:')
    if tag is not None:
        overview['description'] = tag.find_next('dd').text
        
    # Founders
    tag = soup_overview.find('dt', string='Founders:')
    if tag is not None:
        founders_list = tag.find_next('dd').text.split(",")
        overview['founders'] = [x.strip() for x in founders_list]
    
    # Categories
    tag = soup_overview.find('dt', string='Categories:')
    if tag is not None:
        categories_list = tag.find_next('dd').text.split(",")
        overview['categories'] = [x.strip() for x in categories_list]
    
    # Website
    tag = soup_overview.find('dt', string='Website:')
    if tag is not None:
        overview['website'] = tag.find_next('dd').text
        
    #Social
    tag = soup_overview.find('dd', class_="social-links")
    if tag is not None:
        
        overview['social'] = {}
        
        twitter = tag.find('a',class_="twitter")
        if twitter is not None:
            overview['social']['twitter'] = twitter.get('href')
            
        linkedin = tag.find('a',class_="linkedin")
        if linkedin is not None:
            overview['social']['linkedin'] = linkedin.get('href')
            
    # Scrape page "people"
    people = list()
    for div_people in soup_people.find_all('div',class_='people'):
        for info_block in div_people.find_all('div',class_='info-block'):
            h4 = info_block.find('h4')
            a = h4.a   
            name = a.get('data-name')
            link = a.get('href')
            role = info_block.find('h5').text
            
            name = cbscraper.common.myTextStrip(name)
            role = cbscraper.common.myTextStrip(role)
            
            people.append([name, link, role])
                
    # Scrape page "advisors" (get both main advisors and additional one with the same code)
    advisors = list()
    for div_advisors in soup_advisors.find_all('div',class_='advisors'):
        for info_block in div_advisors.find_all('div',class_='info-block'):
            follow_card = info_block.find('a',class_='follow_card')
            name = follow_card.get('data-name')
            link = follow_card.get('data-permalink')
            primary_role = info_block.h5.text #the primary role of this person (may not be related to the company at hand)
            role_in_bod = info_block.h6.text #his role in our company's BoD
            
            name = cbscraper.common.myTextStrip(name)
            primary_role = cbscraper.common.myTextStrip(primary_role)
            role_in_bod = cbscraper.common.myTextStrip(role_in_bod)
            
            advisors.append([name, link, role_in_bod, primary_role])
                
    #Return data
    company_data = {'overview':overview, 'people':people, 'advisors': advisors}
    
    #Write to file
    with open(json_file,'w') as fileh:
        fileh.write(cbscraper.common.jsonPretty(company_data))
    
    return company_data