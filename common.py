from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from PyQt5.QtWebKitWidgets import QWebPage
import os
import random
import time
import sys
import bs4 as bs
import json
import requests

class Client(QWebPage):

    def __init__(self, url):
        self.app = QApplication(sys.argv)
        QWebPage.__init__(self)
        self.loadFinished.connect(self.on_page_load)
        self.mainFrame().load(QUrl(url))
        self.app.exec_()
        
    def on_page_load(self):
        self.app.quit()
        
def jsonPrettyDict(dict_data):
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '))

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
    if (content.find('name="ROBOTS"') >= 0 
    and content.find('"NOINDEX, NOFOLLOW"') >= 0):
        return True
    return False
    
#Get a webpage and save to file (avoid another request)
def getPageSoup(url, filepath, webkit = False):
    
    if os.path.isfile(filepath):
        filecont = ''
        with open(filepath,'r', encoding="utf8") as fileh:
            filecont = fileh.read()
        
        soup = bs.BeautifulSoup(filecont,'lxml')
        
        print(soup)
        
        if(wasRobotDetected(filecont)):
            print("\t[getPage] Pre-saved file contains robot. Removing it...")
            os.unlink(filepath)
        else:
            print("\t[getPage] Returning content from pre-saved file "+filepath)
            return soup
    
    sleep_sec = random.randrange(2,6)
    print("\t[getPage] Waiting "+str(sleep_sec)+" secs then request")
    time.sleep(sleep_sec)
  
    #Use requests
    cont = ''
    if not webkit:
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
        res = requests.get(url, headers=html_headers)
        cont = res.content
    
#    #Use WebKit
#    client_response = Client(url)
#    cont = client_response.mainFrame().toHtml()
#    #print("Response was: "+str(client_response))
#    #print("HTML: "+str(cont))
    
    if cont == '':
        return False

    soup = bs.BeautifulSoup(cont,'lxml')
    #print(soup)
    
    with open(filepath,'wb') as fileh:
        fileh.write(soup.encode('utf8'))
        
    if(wasRobotDetected(soup)):
        print("\t[getPage] ROBOT: I have downloaded a file that contains robot detection: "+filepath)
        return False
    else:
        print("\t[getPage] File downloaded")
        return True
    
