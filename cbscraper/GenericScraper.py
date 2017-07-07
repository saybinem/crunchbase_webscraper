import json
import logging
import os
import random
import smtplib
import time
from abc import ABCMeta, abstractmethod
from email.mime.text import MIMEText

import bs4 as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.remote_connection import LOGGER

# Non modifiable globals
_browser = None
n_requests = 0

#FUNCTIONS

def saveDictToJsonFile(dict_data, json_file):
    with open(json_file, 'w', encoding="utf-8") as fileh:
        fileh.write(jsonPretty(dict_data))

def myTextStrip(str):
    return str.replace('\n', '').strip()

def jsonPretty(dict_data):
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '))

#CLASS ERROR404
class Error404(Exception):
    pass

#CLASS GENERIC SCRAPER
class GenericScraper(metaclass=ABCMeta):
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
    is_firefox_user_profile = True
    profile_path = r"C:\Users\raffa\AppData\Roaming\Mozilla\Firefox\Profiles\4ai6x5sv.default"

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
        self.getBrowser()

    def randSleep(self, min, max):
        # Sleep to avoid robots
        sec = random.randint(min, max)
        logging.info("Sleeping for " + str(sec) + " seconds ...")
        time.sleep(sec)

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
        except:
            logging.error("Unexpected exception during page load. Retrying")
            self.randSleep(self.get_error_sleep_min, self.get_error_sleep_max)
            return self.openURL(url)
        else:
            logging.debug("browser.get(" + url + ") returned without exceptions")

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

    # Get saved HTML code
    # Raises a Error404 exception if the file contains an error 404 page
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
                    logging.warning("Pre-saved file contains 404 error")
                    raise Error404("Error 404 in '" + htmlfile + "'")
                else:
                    logging.debug("Returning content from pre-saved file '" + htmlfile + "'")
                    return html_code

    # Post-load sleep, Check if there are 404 errors, Wait for the presence of an element in a web page
    def waitForPresenceCondition(self, by, value, sleep=True):
        # Post-loading sleep
        if (sleep):
            self.randSleep(self.postload_sleep_min, self.postload_sleep_max)
        else:
            logging.debug("NOT sleeping")
        # Check for 404 error
        html_code = self.getBrowserPageSource()
        if self.is404(html_code):
            logging.info("404 page retrieved. Raising a Error404 exception")
            raise Error404("404 error on page '" + self.getBrowserURL() + "'")
        # Check for robot detection
        if self.wasRobotDetected(html_code):
            self.detectedAsRobot()
        # wait for the presence in the DOM of a tag with a given class
        condition_str = "(" + str(by) + "," + value + ")"
        url = self.getBrowserURL()
        msg = "Waiting for visibility of "
        msg += condition_str
        msg += " in URL='" + url + "'"
        logging.info(msg)
        try:
            condition = EC.visibility_of_element_located((by, value))
            WebDriverWait(self.getBrowser(), self.wait_timeout).until(condition)
        except TimeoutException:
            logging.critical("Timed out waiting for page element. Fatal. Exiting")
            raise
        except:
            logging.error("Unexpected exception waiting for page element. Exiting")
            raise
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
            logging.info("Creating Selenium webdriver")
            LOGGER.setLevel(logging.WARNING)

            ## Firefox user profile
            if self.is_firefox_user_profile:
                profile = webdriver.firefox.firefox_profile.FirefoxProfile(self.firefox_profile_path)
            else:
                profile = webdriver.firefox.firefox_profile.FirefoxProfile()

            _browser = webdriver.firefox.webdriver.WebDriver(firefox_profile=profile)

            ## Firefox new profile
            # cbscraper.common._browser = webdriver.Firefox()

            # Modify windows
            _browser.set_window_position(0, 0)
            # browser.maximize_window()

            # sleep after browser opening
            self.randSleep(2, 3)

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
        with open("email_credentials.json", "r") as fileh:
            credentials = json.load(fileh)

        fromaddr = credentials['email']
        toaddr = credentials['email']
        body = "Scraping is stalled by robot detection"

        msg = MIMEText(body)
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "Stalled by robot"

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
