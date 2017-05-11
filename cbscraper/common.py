import os
import random
import time
import sys
import bs4 as bs
import json
import requests
import codecs
from pprint import pprint

#Selenium imports
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def myTextStrip(str):
    return str.replace('\n','').strip()

def jsonPretty(dict_data):
    return json.dumps(dict_data, sort_keys=False, indent=4, separators=(',', ': '))

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
def myRequest(url):
    
    if(url.find("person") >= 0 ):
        type="person"
    elif(url.find("people") >= 0 ):
        type="org-people"
    elif(url.find("advisors") >= 0 ):
        type="org-advisors"
    elif(url.find("organization") >= 0 ):
        type="org"
    else:
        print("ERROR: url type not recognized "+url)
        exit()
    
    sleep_sec = random.randrange(0, 5)
    #sleep_sec = 0
    
    print("\t[getPageSoup] Waiting "+str(sleep_sec)+" secs")
    time.sleep(sleep_sec)

    #Use selenium
    print("\t[getPageSoup] Running Selenium")
    browser = webdriver.Firefox()
    browser.get(url)
    
#     timeout = 10 # seconds
#     try:
#         element_present = EC.presence_of_element_located((By.ID, 'profile_header_heading'))
#         WebDriverWait(browser, timeout).until(element_present)
#     except TimeoutException:
#         print("Timed out waiting for page to load") 
    
    sleep_time = 18
    print("\t[getPageSoup] Waiting "+str(sleep_time)+" secs")
    time.sleep(sleep_time)
 
    cont = browser.page_source
    browser.quit()
    
    return cont

#Get a webpage and save to file (avoid another request). Return the page soup
def getPageSoup(url, filepath):
    
    if os.path.isfile(filepath):
        
        with codecs.open(filepath, 'r', 'utf-8') as fileh:
            try:
                filecont = fileh.read()
            except UnicodeDecodeError:
                print("UnicodeDecodeError on "+filepath+" redownloading it...")
                fileh.close()
                os.unlink(filepath)
                filecont = ''
        
        if filecont != '':
            if(wasRobotDetected(filecont)):
                print("\t[getPageSoup] Pre-saved file contains robot. Removing it...")
                os.unlink(filepath)
            else:
                print("\t[getPageSoup] Returning content from pre-saved file "+filepath)
                soup = bs.BeautifulSoup(filecont,'lxml')
                return soup
    
    #print("\t[getPageSoup] Requesting origin "+origin_url)
    #myRequest(origin_url)
    
    print("\t[getPageSoup] Requesting actual url "+url)
    cont = myRequest(url)
        
    #Get the soup
    
    #print("type(cont): "+str(type(cont)))
    
    soup = bs.BeautifulSoup(cont,'lxml')       
    cont_str = cont
    
    with codecs.open(filepath, 'w', 'utf-8') as fileh:
        fileh.write(cont)
            
    # Check for robot detection
    if wasRobotDetected(cont_str):
        print("\t[getPageSoup] ROBOT: I have downloaded a file that contains robot detection: "+filepath)
        exit()
    else:
        print("\t[getPageSoup] File downloaded")
        return soup
    
