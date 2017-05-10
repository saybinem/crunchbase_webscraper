import os
import random
import time
import sys
import bs4 as bs
import json
import requests
import codecs
from pprint import pprint

from fake_useragent import UserAgent
ua = UserAgent()

def myTextStrip(str):
    return str.replace('\n','').strip()

def jsonPretty(dict_data):
    return json.dumps(dict_data, sort_keys=False, indent=4, separators=(',', ': '))

def getHtmlHeader(url, origin_url, cookie_data):
    header = {
             'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
             'Accept-Encoding':'gzip, deflate, sdch, br',
             'Accept-Language':'en-US,en;q=0.8,it-IT;q=0.6,it;q=0.4,de;q=0.2,nl;q=0.2,es;q=0.2,ar;q=0.2,pt;q=0.2,fr;q=0.2,ko;q=0.2,sl;q=0.2,cs;q=0.2',
             'Cache-Control':'max-age=0',
             'Connection':'keep-alive',             
             'Host':'www.crunchbase.com',
             'Referer':origin_url,
             'Upgrade-Insecure-Requests':'1',
             #'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
             'User-Agent' : ua.random
                 }
    
    if(cookie_data != ''):
        header['Cookie'] = cookie_data
    
    print("Header: ")
    pprint(header)
    
    return header
    
#check robots
def wasRobotDetected(content):
    
    if (content.find('"ROBOTS"') >= 0 
    and content.find('"NOINDEX, NOFOLLOW"') >= 0):
        print("Robot detected by test 1")
        return True
    
    if (content.find('"robots"') >= 0 
    and content.find('"noindex, nofollow"') >= 0):
        print("Robot detected by test 2")
        return True
    
    if (content.find('Pardon Our Interruption...') >= 0):
        print("Robot detected by test 3")
        return True
    
    return False

#Requesting page with random delay and custom headers
def myRequest(url, origin_url, cookie_data):
    html_headers = getHtmlHeader(url, origin_url, cookie_data)
    sleep_sec = random.randrange(10, 25)
    
    if myRequest.counter > 0:
        print("\t[getPageSoup] Waiting "+str(sleep_sec)+" secs")
        time.sleep(sleep_sec)
    else:
        print("\t[getPageSoup] NO Waiting")
        
    myRequest.counter += 1
    
    #Use requests
    print("\t[getPageSoup] I am using REQUESTS")
    res = requests.get(url, headers=html_headers)
    cont = res.content
    return cont

#Get a webpage and save to file (avoid another request). Return the page soup
def getPageSoup(url, filepath, origin_url, cookie_data):
    
    if os.path.isfile(filepath):
        
        with open(filepath,'rb') as fileh:
            filecont = fileh.read()
        
        filecont_dec = filecont.decode()
        
        if(wasRobotDetected(filecont_dec)):
            print("\t[getPageSoup] Pre-saved file contains robot. Removing it...")
            os.unlink(filepath)
        else:
            print("\t[getPageSoup] Returning content from pre-saved file "+filepath)
            soup = bs.BeautifulSoup(filecont,'lxml')
            return soup
    
    #print("\t[getPageSoup] Requesting origin "+origin_url)
    #myRequest(origin_url)
    
    print("\t[getPageSoup] Requesting actual url "+url)
    cont = myRequest(url, origin_url, cookie_data)
    
    if cont is False:
        return False
        
    #Get the soup
    
    #print("type(cont): "+str(type(cont)))
    
    soup = bs.BeautifulSoup(cont,'lxml')   
    cont_str = soup.decode('utf8')
    
    # Write binary content to file
    with codecs.open(filepath,'wb') as fileh:
        fileh.write(cont)
    
    # Check for robot detection
    if wasRobotDetected(cont_str):
        print("\t[getPageSoup] ROBOT: I have downloaded a file that contains robot detection: "+filepath)
        return False
    else:
        print("\t[getPageSoup] File downloaded")
        return soup
    
