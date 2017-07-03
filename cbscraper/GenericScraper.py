import logging
import os
import random
import time
from abc import ABCMeta, abstractmethod

import bs4 as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import cbscraper.common


class GenericScraper(metaclass=ABCMeta):
    #Time to wait after the successful location of an element
    #Uses in waitForPresenceCondition()
    postload_sleep_min = 5
    postload_sleep_max = 20

    # how much time to sleep after going back
    back_timeout = 20  # seconds before declaring timeout after going back
    load_timeout = 30  # for set_page_load_timeout in openURL()
    wait_timeout = 120  # for WebDriverWait(self.getBrowser(), self.wait_timeout).until(condition)

    wait_robot_min = 10 * 60
    wait_robot_max = 15 * 60

    max_requests_per_browser_instance = 30

    # internal variables
    @property
    @abstractmethod
    def htmlfile_suffix(self):
        pass

    @property
    @abstractmethod
    def cb_url(self):
        pass

    @property
    @abstractmethod
    def link_map(self):
        pass

    @property
    @abstractmethod
    def class_wait(self):
        pass

    @property
    @abstractmethod
    def html_basepath(self):
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

    # return false if we btained a missing link
    def is404(self, html=None):
        if html is None:
            try:
                self.getBrowser().find_element_by_id('error-404')
            except NoSuchElementException:
                return False
            except:
                logging.critical("Unexpected exception in is404()")
                raise
            else:
                return True
        else:
            soup = self.makeSoupFromHTML(html)
            return soup.find('div', id='error-404') is not None

    #Add a browser request and eventually restart the browser
    def addBrowserRequest(self):
        cbscraper.common.n_requests += 1
        if (cbscraper.common.n_requests >= self.max_requests_per_browser_instance):
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
            logging.warning("Timeout exception during page load. Try to continue.")
        except:
            logging.error("Unexpected exception during page load. Exiting.")
            raise
        else:
            logging.debug("browser.get(" + url + ") returned without exceptions")

    def writeHTMLFile(self, html, endpoint):
        htmlfile = self.genHTMLFilePath(endpoint)
        logging.info("Writing " + str(endpoint) + " in " + htmlfile)
        with open(htmlfile, 'w', encoding='utf-8') as fileh:
            fileh.write(html)

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
                filecont = fileh.read()
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
                if (self.wasRobotDetected(filecont)):
                    logging.warning("Pre-saved file contains robot. Removing it")
                    fileh.close()
                    os.unlink(htmlfile)
                    return False
                elif self.is404(filecont):
                    logging.warning("Pre-saved file contains 404 error")
                    return False
                else:
                    logging.debug("Returning content from pre-saved file " + htmlfile)
                    return filecont

    # Check if there is 404 errore, wait for the presence of an element in a web page and then wait for some more time
    def waitForPresenceCondition(self, by, value):
        # Post-loading sleep
        self.randSleep(self.postload_sleep_min, self.postload_sleep_max)
        #Check for 404 error
        if self.is404():
            logging.info("404 page retrieved")
            return False
        #Check for robot detection
        if self.wasRobotDetected():
            self.detectedAsRobot()
        #wait for the presence in the DOM of a tag with a given class
        try:
            logging.info("Waiting for presence of (" + str(by) + "," + value + "). URL=" + self.getBrowser().current_url)
            condition = EC.presence_of_element_located((by, value))
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
        self.waitForPresenceCondition(By.CLASS_NAME, self.class_wait[endpoint])

    def makeSoupFromHTML(self, html):
        return bs.BeautifulSoup(html, 'lxml')

    # Browser functions
    def setBrowser(self, brow):
        cbscraper.common._browser = brow

    def getBrowser(self):
        if cbscraper.common._browser is None:
            # Use selenium
            logging.debug("Creating webdriver")

            #    profile_path = r"C:\Users\raffa\AppData\Roaming\Mozilla\Firefox\Profiles\4ai6x5sv.default"
            #    firefox_profile = webdriver.FirefoxProfile(profile_path)
            #    firefox_profile.set_preference("browser.privatebrowsing.autostart", True)
            #    cbscraper.common._browser = webdriver.Firefox(firefox_profile=firefox_profile)

            ## Firefox new profile
            cbscraper.common._browser = webdriver.Firefox()

            # browser.maximize_window()
            # sleep after browser opening
            self.randSleep(2, 2)

        return cbscraper.common._browser

    # Get HTML source code of a webpage and handle robot detection
    def getBrowserPageSource(self, curr_endpoint=None):
        html = self.getBrowser().page_source
        if (self.wasRobotDetected(html)):
            logging.critical("Robot detected in browser page")
            self.randSleep(self.wait_robot_min, self.wait_robot_max)
            return self.getBrowserPageSource(curr_endpoint)
        else:
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

    # Get link located in the organization 'entity' page
    def getBrowserLink(self, endpoint):
        return self.getBrowser().find_element_by_xpath('//a[@title="' + self.link_map[endpoint] + '"]')

    # If the organization entity page has a link for more of the information in 'endpoint', return that link
    def isMore(self, start_point, link_point):
        return self.getEndpointSoup(start_point).find('a', attrs={'title': self.link_map[link_point]})

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

    # ROBOT detection
    def wasRobotDetected(self, content=None):
        if(content is None):
            content = self.getBrowser().page_source
        if (content.find('"ROBOTS"') >= 0 and content.find('"NOINDEX, NOFOLLOW"') >= 0):
            logging.error("Robot detected by test 1")
            return True
        if (content.find('"robots"') >= 0 and content.find('"noindex, nofollow"') >= 0):
            logging.error("Robot detected by test 2")
            return True
        if (content.find('Pardon Our Interruption...') >= 0):
            logging.error("Robot detected by test 3")
            return True
        return False

    def detectedAsRobot(self):
        logging.info("We were detected as robots")
        try:
            logging.info("Refreshing the page")
            self.getBrowser().refresh()
        except:
            pass
        self.randSleep(5,10)
        detected = self.wasRobotDetected()
        if not detected:
            logging.info("Detection escaped")
            return True
        else:
            logging.info("We are still being detected. Restarting the browser")
            self.restartBrowser()
            self.randSleep(self.wait_robot_min, self.wait_robot_max)
            return self.detectedAsRobot()

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
            logging.critical("Unhandled exception during back. Exitin.")
            exit()