import json
import logging
import os
import random
import smtplib
import time
from abc import ABCMeta, abstractmethod
from email.mime.text import MIMEText

import bs4 as bs
import cbscraper.common
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Non modifiable globals
_browser = None
n_requests=0

class Error404(Exception):
    pass

class GenericScraper(metaclass=ABCMeta):
    # Time to wait after the successful location of an element
    # Uses in waitForPresenceCondition()
    postload_sleep_min = 10
    postload_sleep_max = 20

    # how much time to sleep after going back
    back_timeout = 20  # seconds before declaring timeout after going back
    load_timeout = 40  # for set_page_load_timeout in openURL()
    wait_timeout = 3*60  # for WebDriverWait(self.getBrowser(), self.wait_timeout).until(condition)

    wait_robot_min = 10 * 60
    wait_robot_max = 15 * 60

    max_requests_per_browser_instance = 5000

    # internal variables

    # map a remote endpoint to HTML file suffix
    @property
    @abstractmethod
    def htmlfile_suffix(self):
        pass

    #map an endpoint to a class to wait for
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
            cbscraper.common.n_requests = 0

    # Open an url in web browser
    def openURL(self, url):
        self.addBrowserRequest()
        self.getBrowser().set_page_load_timeout(self.load_timeout)
        try:
            self.getBrowser().get(url)
        except TimeoutException:
            logging.warning("Timeout exception during page load. Moving on.")
        except:
            logging.error("Unexpected exception during page load. Retrying")
            self.randSleep(60, 60)
            return self.openURL(url)
        else:
            logging.debug("browser.get(" + url + ") returned without exceptions")

    # Write HTML to file
    def writeHTMLFile(self, html, endpoint):
        htmlfile = self.genHTMLFilePath(endpoint)
        logging.info("Writing " + str(endpoint) + " in " + htmlfile)
        with open(htmlfile, 'w', encoding='utf-8') as fileh:
            fileh.write(html)

    # Get the file path of local HTML file from remote endpoin
    def genHTMLFilePath(self, endpoint):
        if endpoint not in self.htmlfile_suffix:
            raise RuntimeError("The endpoint you passed is not mapped anywhere")
        return os.path.join(self.html_basepath, self.id + self.htmlfile_suffix[endpoint] + ".html")

    # Get saved HTML code
    def getHTMLFile(self, endpoint):

        htmlfile = self.genHTMLFilePath(endpoint)

        # Check if HTML file already exist
        if not os.path.isfile(htmlfile):
            logging.debug("HTML file " + htmlfile + " not found")
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
                elif self.is404(html_code):
                    logging.warning("Pre-saved file contains 404 error")
                    raise Error404("Error 404 in "+htmlfile)
                else:
                    logging.debug("Returning content from pre-saved file " + htmlfile)
                    return html_code

    # Post-load sleep, Check if there are 404 errors, Wait for the presence of an element in a web page
    def waitForPresenceCondition(self, by, value):
        # Post-loading sleep
        self.randSleep(self.postload_sleep_min, self.postload_sleep_max)
        # Check for 404 error
        html_code = self.getBrowserPageSource()
        if self.is404(html_code):
            logging.info("404 page retrieved")
            raise Error404("404 error on page "+self.getBrowserURL())
        # Check for robot detection
        if self.wasRobotDetected(html_code):
            self.detectedAsRobot()
        # wait for the presence in the DOM of a tag with a given class
        try:
            msg = "Waiting for visibility of "
            msg += "(" + str(by) + "," + value + ")"
            msg += " in URL='" + self.getBrowser().current_url + "'"
            logging.info(msg)
            condition = EC.visibility_of_element_located((by, value))
            WebDriverWait(self.getBrowser(), self.wait_timeout).until(condition)
        except TimeoutException:
            logging.critical("Timed out waiting for page element. Fatal")
            raise
        except:
            logging.error("Unexpected exception waiting for page element. Exiting")
            raise
        else:
            logging.info("Page element correctly found")

    def waitForClass(self, endpoint):
        return self.waitForPresenceCondition(By.CLASS_NAME, self.class_wait[endpoint])

    def makeSoupFromHTML(self, html):
        return bs.BeautifulSoup(html, 'lxml')

    # Browser functions
    def setBrowser(self, brow):
        cbscraper.common._browser = brow

    def getBrowser(self):
        global _browser
        if _browser is None:
            # Use selenium
            logging.debug("Creating webdriver")

            ## FIrefox user profile
            profile_path = r"C:\Users\raffa\AppData\Roaming\Mozilla\Firefox\Profiles\4ai6x5sv.default"
            firefox_profile = webdriver.FirefoxProfile(profile_path)
            # firefox_profile.set_preference("browser.privatebrowsing.autostart", True)
            _browser = webdriver.Firefox(firefox_profile=firefox_profile)

            ## Firefox new profile
            # cbscraper.common._browser = webdriver.Firefox()

            # Modify windows
            _browser.set_window_position(0, 0)
            # browser.maximize_window()

            # sleep after browser opening
            self.randSleep(2, 3)

        return _browser

    # Get HTML source code of a webpage. If curr_endpoint is not None, write the HTML code to a file
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
