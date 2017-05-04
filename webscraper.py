import bs4 as bs
import requests
import os
import json
import re
import time
import random

#class DateInterval
class DateInterval(object):

    def __init__(self):
        return

    def fromText(self, date_text):
        date_text = date_text.split('-')
        self.start = date_text[0].strip()
        if(len(date_text)>1):
            self.end = date_text[1].split(u"\u00A0")[0].strip()
        else:
            self.end = "Current"
            
    def getStart(self):
        return self.start
    
    def getEnd(self):
        return self.end
    
#check robots
def wasRobotDetected(content):
    if content.find('<meta content="NOINDEX, NOFOLLOW" name="ROBOTS"/>') >= 0:
        return True
    return False
    
#Get a webpage and save to file (avoid another request)
def getPageSoup(url, filepath):
    
    if os.path.isfile(filepath):
        filecont = ''
        with open(filepath,'r') as fileh:
            filecont = fileh.read()
            
        if(wasRobotDetected(filecont)):
            print("\t[getPage] Pre-saved file contains robot. Removing it...")
            os.unlink(filepath)
        else:
            print("\t[getPage] Returning content from pre-saved file "+filepath)
            return bs.BeautifulSoup(filecont,'lxml')
    
    # Get a copy of the default headers that requests would use
    #html_headers = requests.utils.default_headers()
    
    # Update the headers with your custom ones
    # You don't have to worry about case-sensitivity with
    # the dictionary keys, because default_headers uses a custom
    # CaseInsensitiveDict implementation within requests' source code.
    html_headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, sdch, br',
            'Accept-Language':'en-US,en;q=0.8,it-IT;q=0.6,it;q=0.4,de;q=0.2,nl;q=0.2,es;q=0.2,ar;q=0.2,pt;q=0.2,fr;q=0.2,ko;q=0.2,sl;q=0.2,cs;q=0.2',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            #'Cookie':'multivariate_bot=false; multivariate_bot=false; D_SID=131.175.28.129:C572Gn0Ju2IzuPfSp7uDAzNJNcNpftVP5fAk1WxmA4g; _vdl=1; __uvt=; AMCV_6B25357E519160E40A490D44%40AdobeOrg=1256414278%7CMCMID%7C02123957256643389932941714766379639408%7CMCAAMLH-1494270639%7C6%7CMCAAMB-1494270639%7CNRX38WO0n5BH8Th-nqAG_A%7CMCAID%7CNONE; __qca=P0-168327626-1493665839942; _pxvid=dd8cbd10-2ea1-11e7-a5fc-db9f37dccdd1; __cfduid=dd7021c84796cc3e3c7170ea5ed8a63191493665842; remember_user_token=W1s3MjExMzVdLCJmRGZiNENQcVN0R1NRS0RUMnpoOSIsIjE0OTM4NTU4MjEuNjUzMDMyNSJd--30d94229573e6568aa574e8366e89aee6cf5faf3; user_intent_path=%2Faccount%2Fsignup%3Fredirect_to%3D%2Fperson%2Fmarc-lore%2Fadd; user_origin_path=%2Fperson%2Fmarc-lore; _site_session=12aeb82115147919d7e444a99fe80d11; multivariate_bot=false; _oklv=1493887355956%2CEuGYroyZ0xLajRXK3F6pZ0N8RE0Paw2b; _okdetect=%7B%22token%22%3A%2214938873562520%22%2C%22proto%22%3A%22https%3A%22%2C%22host%22%3A%22www.crunchbase.com%22%7D; olfsk=olfsk5792054211346169; _okbk=cd4%3Dtrue%2Cvi5%3D0%2Cvi4%3D1493887356778%2Cvi3%3Dactive%2Cvi2%3Dfalse%2Cvi1%3Dfalse%2Ccd8%3Dchat%2Ccd6%3D0%2Ccd5%3Daway%2Ccd3%3Dfalse%2Ccd2%3D0%2Ccd1%3D0%2C; _ok=1554-355-10-6773; wcsid=EuGYroyZ0xLajRXK3F6pZ0N8RE0Paw2b; hblid=gZaKfyxXgRJxhKgB3F6pZ0N8REabaw6b; jaco_uid=68704b16-90ef-4b55-9d7e-6d4cbe495ecd; jaco_referer=; request_method=POST; _hp2_props.973801186=%7B%22Logged%20In%22%3A%22true%22%2C%22Pro%22%3Afalse%7D; _ga=GA1.2.742019326.1493309404; _gid=GA1.2.1513944676.1493887384; s_pers=%20s_getnr%3D1493887384192-Repeat%7C1556959384192%3B%20s_nrgvo%3DRepeat%7C1556959384194%3B; s_cc=true; _hp2_ses_props.973801186=%7B%22ts%22%3A1493887024114%2C%22d%22%3A%22www.crunchbase.com%22%2C%22h%22%3A%22%2F%22%7D; _hp2_id.973801186=%7B%22userId%22%3Anull%2C%22pageviewId%22%3A%227944223492966448%22%2C%22sessionId%22%3A%225304995322054174%22%2C%22identity%22%3A%22raffaelemancuso91%40gmail.com%22%2C%22trackerVersion%22%3A%223.0%22%7D; uvts=5xzLoJ1Q7Yk38sIz; D_PID=67165DB9-8923-323A-A76B-1DC5168D02F2; D_IID=217A5252-0C98-3DD5-9B87-6D8AF96EF359; D_UID=0428853F-5B3E-3450-8B5B-D007FBFB846B; D_HID=W3DRMkb36fMv68ReSfA94EsZncj9J4F4wcDHck8WPuU; D_ZID=36BD3E53-F126-3E31-8D05-F85859D0809F; D_ZUID=0A628A36-104B-3E67-9619-5AFC1DC938F9; _px=eyJ0IjoxNDkzODg3OTI4MzM2LCJzIjp7ImEiOjAsImIiOjB9LCJoIjoiOWU3OWJiMjhjZWNkZjNlNmIzODNkZmViY2NiZjZlNWZiMjQxN2UyZTE0YzdkNjNjNWJkYWI0ZTg4ZmRjZTg3NiJ9',
            'Host':'www.crunchbase.com',
            'Referer':'https://www.crunchbase.com/app/search/companies/50be5abba91fd20625d8fc2863598b81691080d1',
            'Upgrade-Insecure-Requests':'1',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
    }
    
    #print(html_headers)
    
    sleep_sec = random.randrange(2,6)
    print("Requesting the page to the website. Before sleeping for "+str(sleep_sec)+" secs...")
    time.sleep(sleep_sec)
  
    res = requests.get(url, headers=html_headers)

    #print(res.status_code)
    
    cont = res.content
    #print(cont)
    
    soup = bs.BeautifulSoup(cont,'lxml')
    #print(soup)
    
    with open(filepath,'w') as fileh:
        fileh.write(str(soup))
    
    if(wasRobotDetected(filepath)):
        print("[getPage] I have downloaded a file that contains robot detection: "+filepath)
        return False
    else:
        return soup

def jsonPrettyDict(dict_data):
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '))

#Scrape a company
def scrapeOrganization(company_name):
    
    print("Scraping company people "+company_name)
    html_file_people = "./company/html/"+company_name+"_people.html"
    html_file_advisors = "./company/html/"+company_name+"_board.html"
    json_file = "./company/json/"+company_name+".json"
    
    soup_people = getPageSoup('https://www.crunchbase.com/organization/'+company_name+'/people', html_file_people)
    if(soup_people is False):
        return False
    
    soup_advisors = getPageSoup('https://www.crunchbase.com/organization/'+company_name+'/advisors', html_file_advisors)
    if(soup_advisors is False):
        return False
    
    #Get people
    people = list()
    for div in soup_people.find_all('div',class_='people'):
        for ul in div.find_all('ul'):
            for li in ul.find_all('li'):
                info_block = li.find('div',class_='info-block')
                h4 = info_block.find('h4')
                a = h4.a
                h5 = info_block.find('h5')
                name = a.get('data-name')
                link = a.get('href')
                role = h5.text
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
    writeToFile(json_file, jsonPrettyDict(company_data))
    return company_data
    
#Scrape a single person    
#e.g. person_link="/person/gavin-ray"    
def scrapePerson(person_link):
    print("Scraping person: "+person_link)
    person_name = person_link.split('/')[2]

    html_file = "./person/html/"+person_name+".html"
    json_file = "./person/json/"+person_name+".json" #output file
    
    soup = getPageSoup('https://www.crunchbase.com'+person_link, html_file)
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
            date_int = DateInterval()
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
                        date_int = DateInterval()
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
            if date_int is not None:
                date_int_c = DateInterval()
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
    fileh = open(json_file,'w')
    fileh.write(jsonPrettyDict(person_data))
    fileh.close()    

company = "ip-access"
company_data = scrapeOrganization("facebook")

#if(company_data is not False):
#    for key,value in company_data['people'].items():
#        scrapePerson(value['link'])
