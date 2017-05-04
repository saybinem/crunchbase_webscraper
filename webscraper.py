import bs4 as bs
import urllib.request
import requests
from fake_useragent import UserAgent
import os
import json

def getPage(url, filepath):
    
    # Get a copy of the default headers that requests would use
    #html_headers = requests.utils.default_headers()
    
    # Update the headers with your custom ones
    # You don't have to worry about case-sensitivity with
    # the dictionary keys, because default_headers uses a custom
    # CaseInsensitiveDict implementation within requests' source code.
    html_headers = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, br, sdch',
            #'Accept-Language':'en-US,en;q=0.8,it-IT;q=0.6,it;q=0.4,de;q=0.2,nl;q=0.2,es;q=0.2,ar;q=0.2,pt;q=0.2,fr;q=0.2,ko;q=0.2,sl;q=0.2,cs;q=0.2',
            'Connection':'keep-alive',
            #'Cookie':'D_SID=131.175.28.129:C572Gn0Ju2IzuPfSp7uDAzNJNcNpftVP5fAk1WxmA4g; olfsk=olfsk5792054211346169; hblid=gZaKfyxXgRJxhKgB3F6pZ0N8REabaw6b; jaco_uid=68704b16-90ef-4b55-9d7e-6d4cbe495ecd; jaco_referer=; _vdl=1; __uvt=; AMCV_6B25357E519160E40A490D44%40AdobeOrg=1256414278%7CMCMID%7C02123957256643389932941714766379639408%7CMCAAMLH-1494270639%7C6%7CMCAAMB-1494270639%7CNRX38WO0n5BH8Th-nqAG_A%7CMCAID%7CNONE; __qca=P0-168327626-1493665839942; _pxvid=dd8cbd10-2ea1-11e7-a5fc-db9f37dccdd1; __cfduid=dd7021c84796cc3e3c7170ea5ed8a63191493665842; s_sq=%5B%5BB%5D%5D; multivariate_bot=false; _ga=GA1.2.742019326.1493309404; _gid=GA1.2.686581765.1493849684; _gat=1; _gat_newTracker=1; _hp2_props.973801186=%7B%22Logged%20In%22%3A%22false%22%2C%22Pro%22%3Afalse%7D; s_pers=%20s_getnr%3D1493849684237-Repeat%7C1556921684237%3B%20s_nrgvo%3DRepeat%7C1556921684240%3B; s_cc=true; _hp2_ses_props.973801186=%7B%22ts%22%3A1493846382099%2C%22d%22%3A%22www.crunchbase.com%22%2C%22h%22%3A%22%2F%22%7D; _hp2_id.973801186=%7B%22userId%22%3A%227984995244007902%22%2C%22pageviewId%22%3A%227117010994098923%22%2C%22sessionId%22%3A%221191682716175901%22%2C%22identity%22%3Anull%2C%22trackerVersion%22%3A%223.0%22%7D; D_PID=67165DB9-8923-323A-A76B-1DC5168D02F2; D_IID=217A5252-0C98-3DD5-9B87-6D8AF96EF359; D_UID=0428853F-5B3E-3450-8B5B-D007FBFB846B; D_HID=W3DRMkb36fMv68ReSfA94EsZncj9J4F4wcDHck8WPuU; D_ZID=36BD3E53-F126-3E31-8D05-F85859D0809F; D_ZUID=0A628A36-104B-3E67-9619-5AFC1DC938F9; _px=eyJ0IjoxNDkzODUwMDA1MDUxLCJzIjp7ImEiOjAsImIiOjB9LCJoIjoiNzYwMDE5ZTZkZDE2ZDcyM2YxNWI3ODlmOTE5NjEwMDhiNWFjMTZiMzBjYmQ4Njc3MmZlNDllZGE2ODFlNWMyNSJ9; uvts=5xzLoJ1Q7Yk38sIz',
            'Host':'www.crunchbase.com',
            'Referer':'https://www.crunchbase.com/',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
    }
    
    #print(html_headers)
    
    res = requests.get(url, headers=html_headers)

    #print(res.status_code)
    
    cont = res.content
    #print(cont)
    
    soup = bs.BeautifulSoup(cont,'lxml')
    #print(soup)
    
    fileh = open(filepath,'w')
    fileh.write(str(soup))
    fileh.close()

def readFromFile(file):
    fileh = open(file,'r')
    str = fileh.read()
    fileh.close()
    return str

def scrapeCompany(company_name):
    
    html_file = company_name+".html"
    if not os.path.isfile(html_file):
        getPage('https://www.crunchbase.com/organization/'+company_name+'/people', html_file)

    filecont = readFromFile(html_file)
    soup = bs.BeautifulSoup(filecont,'lxml')
    #print(soup)
    people = dict()

    for div in soup.find_all('div',class_='people'):
        for ul in div.find_all('ul'):
            for li in ul.find_all('li'):
                info_block = li.find('div',class_='info-block')
                h4 = info_block.find('h4')
                a = h4.a
                h5 = info_block.find('h5')
                name = a.get('data-name')
                link = a.get('href')
                role = h5.text
                people.update({ name: { 'link': link, 'role':role }  })
                
    return people

def scrapePerson(person_name):
    
    html_file = person_name+".html"
    if not os.path.isfile(html_file):
        getPage('https://www.crunchbase.com/person/'+person_name, html_file)

    filecont = readFromFile(html_file)
    soup = bs.BeautifulSoup(filecont,'lxml')
    #print(soup)
    
    #Get current jobs
    current_jobs = dict()
    for current_job in soup.find_all('div',class_='current_job'):
        info_block = current_job.find('div',class_='info-block')
        role = info_block.h4.text
        follow_card = info_block.find('a',class_='follow_card')
        firm = follow_card.text
        current_jobs.update({firm: {'role':role}})
        date = info_block.find('h5',class_='date')
        if(date is not None):
            date_text = date.text.split('-')
            start = date_text[0].strip()
            end = date_text[1].split(u"\u00A0")[0].strip()
            current_jobs[firm].update({'from':start,'to':end})
    
    #Get advisory roles
    adv_roles = dict()
    for advisory_role in soup.find_all('div',class_='advisory_roles'):
        for li in advisory_role.ul.find_all('li'):
            info_block = li.div
            role = info_block.h5.text
            firm = info_block.h4.a.text
            adv_roles.update({firm: {'role':role}})
            date = info_block.find('h5',class_='date')
            if(date is not None):
                date_text = date.text
                if date_text:
                    print("'"+date_text+"'")
                    date_text = date_text.split('-')
                    start = date_text[0].strip()
                    end = date_text[1].split(u"\u00A0")[0].strip()
                    adv_roles[firm].update({'from':start,'to':end})
    
    #Build complete dictionary
    info = {'current_jobs':current_jobs, "advisory_roles":adv_roles}
    
    fileh = open(person_name+".json",'w')
    fileh.write(json.dumps(info, sort_keys=True, indent=4, separators=(',', ': ')))
    fileh.close()
    
    print(current_jobs)

#people = scrapeCompany("ip-access")
#print(people)

scrapePerson("mark-zuckerberg")