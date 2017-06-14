import cbscraper.common
import re
import os
import json
from pprint import pprint
import cbscraper.DateInterval
import codecs

def getPersonIdFromLink(link):
    return link.split("/")[2]

#Scrape a single person    
#e.g. person_link="/person/gavin-ray"    
def scrapePerson(data):
    
    # Get vars
    person_id = data['id']
    overview_html = data['overview']
    json_file = data['json']
    rescrape = data['rescrape']
    type = data['type']
    
    company_cb_id = data['company_id_cb']
    company_vico_id = data['company_id_vico']
    
    if(os.path.isfile(json_file) and not rescrape):
        print("[scrapePerson] Person \""+person_id+"\" already scraped")
        return True
    
    print("[scrapePerson] Scraping person: \""+person_id+"\"")
    person_link = "/person/"+person_id
    
    # Get the soup
    soup = cbscraper.common.getPageSoup('https://www.crunchbase.com'+person_link, overview_html)
    if(soup is False):
        print("Error during person soup")
        return False
    
    #Get name
    name = soup.find(id='profile_header_heading').text
    
    #Get overview information
    overview = dict()
    overview_content = soup.find(id='info-card-overview-content')
    
    if overview_content is not None:
        
        # Primary role
        tag = overview_content.find('dt', string='Primary Role')
        if tag is not None:
            role_arr = tag.find_next('dd').text.split('@')
            overview['primary_role'] = dict()
            overview['primary_role']['role'] = role_arr[0].strip()
            overview['primary_role']['firm'] = role_arr[1].strip()
            
        # Born date
        tag = overview_content.find('dt', string='Born:')
        if tag is not None:
            overview['born'] = tag.find_next('dd').text
        
        # Gender
        tag = overview_content.find('dt', string='Gender:')
        if tag is not None:
            overview['gender'] = tag.find_next('dd').text

        # Location
        tag = overview_content.find('dt', string='Location:')
        if tag is not None:
            overview['location'] = tag.find_next('dd').text
        
        #Social links
        overview['social'] = dict()
        tag = overview_content.find('dt', text=re.compile('Social:.*'))
        if tag:
            social_links = tag.findNext('dd')
            
            a_tag = social_links.find('a',{'data-icons':'facebook'})
            if a_tag is not None:
                overview['social']['facebook'] = a_tag.get('href')
            
            a_tag = social_links.find('a',{'data-icons':'linkedin'})
            if a_tag is not None:
                overview['social']['linkedin'] = a_tag.get('href')
            
            a_tag = social_links.find('a',{'data-icons':'twitter'})
            if a_tag is not None:
                overview['social']['twitter'] = a_tag.get('href')

    #Get personal details (in HTML code they are called 'description')
    person_details = ''
    div_description = soup.find('div',{"id": "description"})
    if div_description is not None:
        person_details = div_description.text
    
    #Get current jobs
    current_jobs = list()
    for current_job in soup.find_all('div',class_='current_job'):
        info_block = current_job.find('div',class_='info-block')
        role = info_block.h4.text
        follow_card = info_block.find('a',class_='follow_card')
        company = follow_card.text        
        job_items = [role,company]        
        date = info_block.find('h5',class_='date')
        date_start, date_end = '', ''
        if(date is not None):
            date_text = date.text
            date_int = cbscraper.DateInterval.DateInterval()
            date_int.fromText(date_text)
            date_start, date_end = date_int.getStart(), date_int.getEnd()
        current_jobs.append([role, company, date_start, date_end])    
    
    #Get past jobs
    past_jobs = list()
    for div_past_job in soup.find_all('div',class_='past_job'):        
        #recursive=False finds only DIRECT children of the div
        for info_row in div_past_job.find_all('div',class_='info-row', recursive=False):            
            #skip header and footer
            if info_row.find('div',class_=['header','footer'], recursive=False) is not None:
                #print("HEADER OR FOOTER FOUND")
                continue            
            date_start_child = info_row.find('div',class_='date')
            date_start = date_start_child.text
            date_end = date_start_child.find_next('div',class_='date').text
            title = info_row.find('div',class_='title').text
            company = info_row.find('div',class_='company').text        
            past_jobs.append([company, title, date_start, date_end])            
            #print("Found past job: "+str(past_job_dict))
                        
    #Get advisory roles
    adv_roles = list()
    for advisory_role in soup.find_all('div',class_='advisory_roles'):
        advisory_role_ul = advisory_role.ul
        if advisory_role_ul is not None:
            for li in advisory_role_ul.find_all('li'):
                info_block = li.div
                role = info_block.h5.text
                company = info_block.h4.a.text
                date = info_block.find('h5',class_='date')
                date_start, date_end = '', ''
                if(date is not None):
                    date_text = date.text
                    if date_text:
                        date_int = cbscraper.DateInterval.DateInterval()
                        date_int.fromText(date_text)
                        date_start, date_end = date_int.getStart(), date_int.getEnd()
                adv_roles.append([role, company, date_start, date_end])    
    
    #Get education
    education = list()
    for edu in soup.find_all('div', class_='education'):
        for info_block in edu.find_all('div',class_='info-block'):
            
            # School
            institute = ''
            if info_block.h4 is not None:
                institute = info_block.h4.a.text
            
            # Subject
            subject = ''
            if info_block.h5 is not None:
                subject = info_block.h5.text   
            
            # Date             
            date_start, date_end = '',''            
            if info_block.h5 is not None:
                date_int = info_block.h5.next_sibling            
                if date_int is not None:
                    date_int_c = cbscraper.DateInterval.DateInterval()
                    date_int_c.fromText(date_int)
                    date_start, date_end = date_int_c.getStart(), date_int_c.getEnd()
                    
            #Put in list       
            edu_items = [institute, subject, date_start, date_end]            
            education.append (edu_items)
    
    #Build complete data set
    person_data = {
            'name': name,
            'type': type,
            'person_id_cb':person_id,
            'company_id_cb':company_cb_id,
            'company_id_vico':company_vico_id,
            'overview':overview, 
            'person_details':person_details, 
            'current_jobs':current_jobs, 
            'past_jobs':past_jobs,
            'advisory_roles':adv_roles,
            'education':education
            }
    
    # Save to JSON file
    with codecs.open(json_file,'w', "utf-8") as fileh:
        fileh.write(cbscraper.common.jsonPretty(person_data))
        
    #Return
    return person_data

        