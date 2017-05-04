import common
import re

#Scrape a single person    
#e.g. person_link="/person/gavin-ray"    
def scrapePerson(person_link):
    print("Scraping person: "+person_link)
    person_name = person_link.split('/')[2]

    html_file = "./person/html/"+person_name+".html"
    json_file = "./person/json/"+person_name+".json" #output file
    
    soup = common.getPageSoup('https://www.crunchbase.com'+person_link, html_file)
    if(soup is False):
        return False
    
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

        # ocation
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
            date_int = common.DateInterval()
            date_int.fromText(date_text)
            date_start, date_end = date_int.getStart(), date_int.getEnd()
        current_jobs.append([role,company, date_start, date_end])    
    
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
            past_jobs.append([
                    company,
                    title,
                    date_start,
                    date_end
                    ])            
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
                        date_int = common.DateInterval()
                        date_int.fromText(date_text)
                        date_start, date_end = date_int.getStart(), date_int.getEnd()
                adv_roles.append([role, company, date_start, date_end])    
    
    #Get education
    education = list()
    for edu in soup.find_all('div', class_='education'):
        for info_block in edu.find_all('div',class_='info-block'):
            institute = info_block.h4.a.text
            subject = info_block.h5.text            
            date_start, date_end = '',''
            date_int = info_block.h5.next_sibling
            print("Education date_int="+repr(date_int)+"("+str(type(date_int))+")")
            if date_int is not None:
                date_int_c = common.DateInterval()
                date_int_c.fromText(date_int)
                date_start, date_end = date_int_c.getStart(), date_int_c.getEnd()
            edu_items = [institute, subject, date_start, date_end]
            #print("Found education "+str(edu_items))
            education.append (edu_items)
    
    #Build complete data set
    person_data = {
            'overview':overview, 
            'person_details':person_details, 
            'current_jobs':current_jobs, 
            'past_jobs':past_jobs,
            'advisory_roles':adv_roles,
            'education':education
            }
    
    #Save to file
    with open(json_file,'w') as fileh:
        fileh.write(common.jsonPrettyDict(person_data))
        