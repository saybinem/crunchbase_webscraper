import json
import logging
import os
import random
import smtplib
import time
from abc import ABCMeta, abstractmethod
from email.mime.text import MIMEText
from enum import Enum

import jsonpickle
import pickle

import bs4 as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.chrome.options import Options as ChromeOptions

from fake_useragent import UserAgent
ua = UserAgent()

import cbscraper.CBPersonData
from cbscraper import global_vars

# Non modifiable globals
_browser = None
n_requests = 0

#FUNCTIONS



def readJSONFile(file):
    if not os.path.isfile(file):
        logging.critical("File not found '"+file+"'")
        assert(False)
    if global_vars.usepickle:
        with open(file, 'rb') as fileh:
            ob = pickle.load(fileh)
    else:
        with open(file, 'r', encoding="utf-8") as fileh:
            #logging.debug(cont)
            cont = fileh.read()
            ob = jsonpickle.decode(cont)
    return ob

def genFullFilename(filename):
    if global_vars.usepickle:
        filename += '.pkl'
    else:
        filename += '.json'
    return filename

#filename DOES NOT INCLUDE EXTENSION
def saveJSON(data, filename):
    if global_vars.usepickle:
        with open(filename, 'wb') as fileh:
            pickle.dump(data, fileh, pickle.HIGHEST_PROTOCOL)
    else:
        with open(filename, 'w', encoding="utf-8") as fileh:
            #logging.info(data.__dict__)
            data_str = jsonpickle.encode(data)
            fileh.write(data_str)

def myTextStrip(str):
    return str.replace('\n', '').strip()

def jsonPretty(dict_data):
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

#CLASS ERROR404

class ErrorNoLink(Exception):
    pass

class Error404(Exception):
    pass

class ErrorInvalidLink(Exception):
    pass

#ENUM BROWSER
class EBrowser(Enum):
    FIREFOX = 1
    PHANTOMJS = 2
    CHROME = 3
    OPERA = 4
    CHROME_HEADLESS = 5

#CLASS GENERIC WEB SCRAPER
class GenericWebScraper(metaclass=ABCMeta):

    # SLEEP VARIABLES
    wait_robot_min = 10 * 60
    wait_robot_max = 15 * 60

    get_error_sleep_min = 2 * 60
    get_error_sleep_max = 5 * 60

    postload_sleep_min = 5  # Time to wait after the successful location of an element. Used in waitForPresenceCondition()
    postload_sleep_max = 10

    # LOAD TIMEOUTS VARIABLES
    back_timeout = 20  # seconds before declaring loading timeout after going back
    load_timeout = 40  # for set_page_load_timeout in openURL()
    wait_timeout = 3 * 60  # for WebDriverWait in waitForPresenceCondition()

    # OTHER VARIABLES
    max_requests_per_browser_instance = 10000
    browser_user_profile = True
    browser_type = EBrowser.FIREFOX

    firefox_profile_path = r"C:\Users\raffa\AppData\Roaming\Mozilla\Firefox\Profiles\4ai6x5sv.default"
    firefox_binary = r"C:\Program Files\Mozilla Firefox\firefox.exe"

    chrome_binary = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    phantomjs_binary = r"C:\data\programmi\phantomjs-2.1.1-windows\bin\phantomjs.exe"

    # internal variables

    # map a remote endpoint to HTML file suffix
    @property
    @abstractmethod
    def htmlfile_suffix(self):
        pass

    # map an endpoint to a class to wait for
    @property
    @abstractmethod
    def class_wait(self):
        pass

    # a strin containing the directory of HTML files
    @property
    @abstractmethod
    def html_basepath(self):
        pass

    @abstractmethod
    def wasRobotDetected(self, filecont):
        pass

    @abstractmethod
    def is404(self, html):
        pass

    @abstractmethod
    def detectedAsRobot(self, filecont):
        pass

    def __init__(self, id):
        self.endpoint_html = dict()
        self.endpoint_soup = dict()
        self.id = id
        LOGGER.setLevel(logging.WARNING) #remove Selenium logging

    def saveScreenshot(self, filename):
        logging.info("Saving current page screenshot in '"+filename+"'")
        self.getBrowser().save_screenshot(filename)

    def sleep(self, sec):
        logging.info("Sleeping for " + str(sec) + " seconds ...")
        time.sleep(sec)

    def randSleep(self, min, max):
        sec = random.randint(min, max)
        self.sleep(sec)

    # Add a browser request and eventually restart the browser
    def addBrowserRequest(self):
        global n_requests
        n_requests += 1
        if (n_requests >= self.max_requests_per_browser_instance):
            logging.info("Reached max num of requests. Restarting the browser")
            self.restartBrowser()
            n_requests = 0

    # Open an url in web browser
    def openURL(self, url):
        self.addBrowserRequest()
        self.getBrowser().set_page_load_timeout(self.load_timeout)
        try:
            logging.debug("Calling browser.get('" + url + "')")
            self.getBrowser().get(url)
        except TimeoutException:
            logging.warning("Timeout exception during page load. Moving on.")
        except Exception as e:
            logging.error("Unexpected exception during page load. "+str(e))
            self.randSleep(self.get_error_sleep_min, self.get_error_sleep_max)
            return self.openURL(url)
        else:
            logging.debug("browser.get('" + url + "') returned without exceptions")

    # Write HTML to file
    def writeHTMLFile(self, html, endpoint):
        htmlfile = self.genHTMLFilePath(endpoint)
        logging.info("Writing " + str(endpoint) + " in '" + os.path.abspath(htmlfile) + "'")
        with open(htmlfile, 'w', encoding='utf-8') as fileh:
            fileh.write(html)

    # Get the file path of local HTML file from remote endpoin
    def genHTMLFilePath(self, endpoint):
        if endpoint not in self.htmlfile_suffix:
            raise RuntimeError("The endpoint you passed is not mapped anywhere")
        path = os.path.join(self.html_basepath, self.id + self.htmlfile_suffix[endpoint] + ".html")
        path = os.path.abspath(path)
        path = os.path.normpath(
            path)  # normalize path which has mixed slashes (e.g. C:\data/ciao -> c:/data/cia0). Only a visual perk for the logs
        return path

    def removeHTMLFile(self, endpoint):
        htmlfile = self.genHTMLFilePath(endpoint)
        if os.path.isfile(htmlfile):
            logging.debug("Removing HTML file for endpoint "+str(endpoint))
            os.remove(htmlfile)

    # Get saved HTML code
    # Raises a Error404 exception if the file contains an error 404 page
    # Return values:
    # - False if HTML file not found (was never downloaded) or file not readable
    # - The HTML source code if the file was found and is readable
    # - Raises Error404 if the file contains a 404 error
    def getHTMLFile(self, endpoint):

        htmlfile = self.genHTMLFilePath(endpoint)

        # Check if HTML file already exist
        if not os.path.isfile(htmlfile):
            logging.debug("HTML file '" + htmlfile + "' not found. Returning False")
            return False

        # Check if we can read from the file
        with open(htmlfile, 'r', encoding='utf-8') as fileh:
            try:
                html_code = fileh.read()
            except UnicodeDecodeError:
                logging.error("UnicodeDecodeError on " + htmlfile + ". Re-downloading it...")
                fileh.close()
                os.unlink(htmlfile)
                return False
            except:
                logging.error("Unhandled exception while reading HTML file")
                raise
            else:
                # Check if the page served was the one for robots
                if (self.wasRobotDetected(html_code)):
                    logging.warning("Pre-saved file contains robot. Removing it")
                    fileh.close()
                    os.unlink(htmlfile)
                    return False
                # Check for 404 error
                elif self.is404(html_code):
                    logging.debug("Pre-saved file contains 404 error")
                    raise Error404("Error 404 in '" + htmlfile + "'")
                else:
                    logging.debug("Returning content from pre-saved file '" + htmlfile + "'")
                    return html_code

    # Post-load sleep, Check if there are 404 errors, Wait for the presence of an element in a web page
    def waitForInvisibility(self, by, value):
        condition_str = "(" + str(by) + "," + value + ")"
        url = self.getBrowserURL()
        msg = "Waiting for in-visibility of "
        msg += condition_str
        msg += " in URL='" + url + "'"
        logging.info(msg)
        try:
            condition = EC.invisibility_of_element_located((by, value))
            WebDriverWait(self.getBrowser(), self.wait_timeout).until(condition)
        except TimeoutException:
            logging.critical("Timed out waiting for element invisibility. Exiting")
            raise
        except:
            logging.error("Unexpected exception waiting for element invisibility. Exiting")
            raise
        else:
            logging.debug("Element " + condition_str + " is now invisible in URL='" + url + "'")

    # Post-load sleep, Check if there are 404 errors, Wait for the presence of an element in a web page
    def waitForPresenceCondition(self, by, value, sleep = True, check_for_errors = True):
        # Post-loading sleep
        if sleep:
            self.randSleep(self.postload_sleep_min, self.postload_sleep_max)
        else:
            logging.debug("NOT sleeping")
        html_code = self.getBrowserPageSource()
        # Check for errors
        if check_for_errors:
            # Check for 404
            if self.is404(html_code):
                msg = "404 error on page '" + self.getBrowserURL() + "'"
                logging.info(msg)
                raise Error404(msg)
            # Check for robot detection
            if self.wasRobotDetected(html_code):
                self.detectedAsRobot()
        # Wait for the presence in the DOM of a tag with a given class
        condition_str = "(" + str(by) + "," + value + ")"
        url = self.getBrowserURL()
        msg = "Waiting for presence of " + condition_str + " in URL='" + url + "'"
        logging.info(msg)
        try:
            condition = EC.presence_of_element_located((by, value))
            WebDriverWait(self.getBrowser(), self.wait_timeout).until(condition)
        except TimeoutException as e:
            logging.critical("Timed out waiting for page element")
            raise e
        except Exception as e:
            logging.critical("Unexpected exception waiting for page element. Exiting")
            raise e
        else:
            logging.debug("Element " + condition_str + " found in URL='" + url + "'")

    def waitForClass(self, endpoint, sleep=True):
        return self.waitForPresenceCondition(By.CLASS_NAME, self.class_wait[endpoint], sleep)

    def makeSoupFromHTML(self, html):
        return bs.BeautifulSoup(html, 'lxml')

    # Browser functions
    def setBrowser(self, brow):
        global _browser
        _browser = brow

    def getBrowser(self):
        global _browser
        if _browser is None:
            # Use selenium
            logging.info("Creating Selenium webdriver using "+str(self.browser_type))

            # FIREFOX
            if self.browser_type == EBrowser.FIREFOX:
                binary = FirefoxBinary(self.firefox_binary)
                #see http://selenium-python.readthedocs.io/faq.html#how-to-auto-save-files-using-custom-firefox-profile
                if self.browser_user_profile:
                    profile = webdriver.FirefoxProfile(self.firefox_profile_path)
                else:
                    profile = webdriver.FirefoxProfile()
                _browser = webdriver.Firefox(firefox_binary=binary, firefox_profile=profile)
                self.sleep(1)
                _browser.set_window_position(0, 0)

            # PHANTOMJS
            elif self.browser_type == EBrowser.PHANTOMJS:
                dcap = dict(DesiredCapabilities.PHANTOMJS)
                useragent = ua.random
                dcap["phantomjs.page.settings.userAgent"] = useragent
                logging.info("Useragent='"+useragent+"'")
                _browser = webdriver.PhantomJS(executable_path=self.phantomjs_path, desired_capabilities=dcap)
                self.sleep(1)
                _browser.set_window_size(1920, 1080)
                self.sleep(1)

            # CHROME
            elif self.browser_type == EBrowser.CHROME:
                _browser = webdriver.Chrome()
                self.sleep(1)
                _browser.set_window_position(0, 0)

            # CHROME (headless)
            elif self.browser_type == EBrowser.CHROME_HEADLESS:
                chrome_options = ChromeOptions()
                chrome_options.add_argument("--headless")
                chrome_options.binary_location = self.chrome_binary
                _browser = webdriver.Chrome(chrome_options=chrome_options)
                self.sleep(1)
                _browser.set_window_position(0, 0)

            # OPERA
            elif self.browser_type == EBrowser.OPERA:
                _browser = webdriver.Opera()
                self.sleep(1)
                _browser.set_window_position(0, 0)

        return _browser

    # Get the HTML source code of a web page. If curr_endpoint is not None, write the HTML code to a file
    def getBrowserPageSource(self, curr_endpoint=None):
        html = self.getBrowser().page_source
        if curr_endpoint is not None:
            self.writeHTMLFile(html, curr_endpoint)
        return html

    # Click on a link and handle exception
    def clickLink(self, link):
        try:
            link.click()
        except TimeoutException:
            logging.error("Timeout exception after a click. Continuing")
        except:
            logging.critical("Unhandled exception after a click. Dying")
            raise

    # Getters / Setters for HTML
    def getEndpointHTML(self, endpoint):
        if endpoint in self.endpoint_html:
            return self.endpoint_html[endpoint]
        else:
            return False

    def setEndpointHTML(self, endpoint, html):
        self.endpoint_html[endpoint] = html

    # Getterss/Setters for soup
    def getEndpointSoup(self, endpoint):
        if endpoint in self.endpoint_soup:
            return self.endpoint_soup[endpoint]
        else:
            return False

    def setEndpointSoup(self, endpoint, soup):
        self.endpoint_soup[endpoint] = soup

    def restartBrowser(self):
        logging.info("Restarting the browser")
        self.getBrowser().quit()
        self.setBrowser(None)
        self.getBrowser()

    def goBack(self):
        try:
            self.getBrowser().set_page_load_timeout(self.back_timeout)
            self.getBrowser().back()
        except TimeoutException:
            logging.warning("Timeout exception during back(). Try to continue.")
        except:
            logging.critical("Unhandled exception during back. Exiting.")
            exit()

    def getBrowserTitle(self):
        return self.getBrowser().title

    def getBrowserURL(self):
        return self.getBrowser().current_url

    def sendRobotEmail(self):
        logging.info("Sending email telling we are stalled by robot detection")
        body = "Scraping is stalled by robot detection"
        subject = "Stalled by robot"
        self.sendEmail(subject, body)

    def sendEmail(self, subject, body):
        with open("email_credentials.json", "r") as fileh:
            credentials = json.load(fileh)

        fromaddr = credentials['email']
        toaddr = credentials['email']

        msg = MIMEText(body)
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = subject

        # SMTP connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(credentials['username'], credentials['password'])
        server.send_message(msg)
        server.quit()

    def browserRefresh(self):
        try:
            self.getBrowser().refresh()
        except Exception as e:
            logging.error("Exception during page refresh. Continuining. " + str(e))
            pass

    def jsScrollDown(self, value):
        self.getBrowser().execute_script("window.scrollBy(0," + str(value) + ")")

    # Scroll down the page
    def scrollDownAllTheWay(self):
        old_page = self.getBrowserPageSource()
        while True:
            logging.debug("Scrolling loop")
            for i in range(2):
                self.jsScrollDown(500)
                #self.jsScrollToBottom()
                self.randSleep(2,3)
            new_page = self.getBrowserPageSource()
            if new_page != old_page:
                old_page = new_page
            else:
                break
        return True

    def jsClick(self, element):
        self.getBrowser().execute_script("arguments[0].click();", element)

    def jsScrollToTop(self):
        self.getBrowser().execute_script("window.scrollTo(0, 0);")

    def jsScrollToBottom(self):
        script = 'window.scrollTo(0, document.body.scrollHeight);'
        self.getBrowser().execute_script(script)
