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
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '))

def getHtmlHeader(url, origin_url):
    header = {
             'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
             'Accept-Encoding':'gzip, deflate, sdch, br',
             'Accept-Language':'en-US,en;q=0.8,it-IT;q=0.6,it;q=0.4,de;q=0.2,nl;q=0.2,es;q=0.2,ar;q=0.2,pt;q=0.2,fr;q=0.2,ko;q=0.2,sl;q=0.2,cs;q=0.2',
             'Cache-Control':'max-age=0',
             'Connection':'keep-alive',
             'Cookie':'D_SID=131.175.28.129:C572Gn0Ju2IzuPfSp7uDAzNJNcNpftVP5fAk1WxmA4g; _vdl=1; __cfduid=dc1f0f0196b05b40633653d3653f0ca131494255068; AMCV_6B25357E519160E40A490D44%40AdobeOrg=1256414278%7CMCMID%7C55164647426195568089190820075558769713%7CMCAID%7CNONE%7CMCAAMLH-1494859871%7C6%7CMCAAMB-1494859871%7CNRX38WO0n5BH8Th-nqAG_A; _pxvid=c5ddf650-33fd-11e7-940f-a1f171579f34; __qca=P0-1641809035-1494255072837; __uvt=; uvts=5zhU7BqhNRd6fqMS; _site_session=689fa544c4d855797a5c359af8cc8388; _oklv=1494347199646%2CBJtR7rfKuwCEPMUX3F6pZ0N8RE0PAba3; _okdetect=%7B%22token%22%3A%2214943472005180%22%2C%22proto%22%3A%22https%3A%22%2C%22host%22%3A%22www.crunchbase.com%22%7D; olfsk=olfsk12119930329147466; _okbk=cd4%3Dtrue%2Cvi5%3D0%2Cvi4%3D1494347200764%2Cvi3%3Dactive%2Cvi2%3Dfalse%2Cvi1%3Dfalse%2Ccd8%3Dchat%2Ccd6%3D0%2Ccd5%3Daway%2Ccd3%3Dfalse%2Ccd2%3D0%2Ccd1%3D0%2C; _ok=1554-355-10-6773; wcsid=BJtR7rfKuwCEPMUX3F6pZ0N8RE0PAba3; hblid=Ix4YBSKFAvJwYFYV3F6pZ0N8REwb32k3; jaco_uid=26681d86-85af-4590-b582-b9877651bc78; jaco_referer=; request_method=POST; multivariate_bot=false; s_sq=%5B%5BB%5D%5D; _hp2_props.973801186=%7B%22Logged%20In%22%3A%22false%22%2C%22Pro%22%3Afalse%7D; _ga=GA1.2.624521533.1494255065; _gid=GA1.2.1000247139.1494347559; s_pers=%20s_getnr%3D1494347560036-Repeat%7C1557419560036%3B%20s_nrgvo%3DRepeat%7C1557419560040%3B; s_cc=true; _hp2_id.973801186=%7B%22userId%22%3A%228076387456068947%22%2C%22pageviewId%22%3A%222671713269691811%22%2C%22sessionId%22%3A%224616769956894929%22%2C%22identity%22%3Anull%2C%22trackerVersion%22%3A%223.0%22%7D; D_PID=67165DB9-8923-323A-A76B-1DC5168D02F2; D_IID=217A5252-0C98-3DD5-9B87-6D8AF96EF359; D_UID=0428853F-5B3E-3450-8B5B-D007FBFB846B; D_HID=W3DRMkb36fMv68ReSfA94EsZncj9J4F4wcDHck8WPuU; D_ZID=6C0A628A-165F-3DED-AAD9-3B9FC7B03A4A; D_ZUID=E7749FA5-0A70-367B-BFA4-67F44C51DABB; _px=eyJzIjp7ImEiOjAsImIiOjB9LCJ0IjoxNDk0MzUwMDQ4MTk4LCJoIjoiYTQxN2QwOTRiZjRhYmQ1NDUwOGIxYjRjNDlhZTIwZTNhZDk1ZDFlOGVkMzgxMTIyMjRiOTI3YjQ5MjM5MTE4NiJ9',
             'Host':'www.crunchbase.com',
             'Referer':origin_url,
             'Upgrade-Insecure-Requests':'1',
             'User-Agent':ua.random
             }
    return header
    
#class DateInterval
class DateInterval(object):

    def __init__(self):
        return

    def fromText(self, date_text):
        date_text = date_text.strip('\n\t ')
        if(len(date_text) == 0):
            self.start = "Unknown"
            self.end = "Unknown"
            return
        date_text = date_text.split('-')
        self.start = date_text[0].strip()
        if(len(date_text)>1):
            self.end = date_text[1].split(u"\u00A0")[0].strip()
        else:
            self.end = "Unknown"
            
    def getStart(self):
        return self.start
    
    def getEnd(self):
        return self.end
    
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
def myRequest(url, origin_url):
    html_headers = getHtmlHeader(url, origin_url)
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

#Get a webpage and save to file (avoid another request)
def getPageSoup(url, filepath, origin_url):
    
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
    cont = myRequest(url, origin_url)
    
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
    
