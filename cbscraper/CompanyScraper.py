import logging
import os
import random
import time
from enum import Enum

import bs4 as bs
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import cbscraper.common


class OrgEndPoint(Enum):
    ENTITY = 'entity'
    PEOPLE = 'people'
    ADVISORS = 'advisors'
    PAST_PEOPLE = 'past_people'


class CompanyScraper():
    postload_sleep_min = 10
    postload_sleep_max = 20

    back_sleep_min = 2
    back_sleep_max = 6

    load_timeout = 60  # for set_page_load_timeout
    wait_timeout = 60  # for WebDriverWait(self.getBrowser(), self.wait_timeout).until(condition)

    wait_robot_min = 10 * 60
    wait_robot_max = 15 * 60

    # Name of the class to wait for when we load a page
    class_wait = {
        OrgEndPoint.ENTITY: 'entity',
        OrgEndPoint.PAST_PEOPLE: 'past_people',
        OrgEndPoint.PEOPLE: 'people',
        OrgEndPoint.ADVISORS: 'advisors',
    }

    # Suffixes of HTML files
    htmlfile_suffix = {
        OrgEndPoint.ENTITY: '_overview',
        OrgEndPoint.PEOPLE: '_people',
        OrgEndPoint.ADVISORS: '_board',
        OrgEndPoint.PAST_PEOPLE: '_past_people',
    }

    # Title attribute of the link tags in the organization 'entity' page
    link_map = {
        OrgEndPoint.PEOPLE: 'All Current Team',
        OrgEndPoint.ADVISORS: 'All Board Members and Advisors',
        OrgEndPoint.PAST_PEOPLE: 'All Past Team'
    }

    # internal variables
    endpoint_html = dict()
    endpoint_soup = dict()

    # last '/' is included
    cb_organization_url = "https://www.crunchbase.com/organization/"

    def __init__(self, company_id, html_basepath):
        self.company_id = company_id
        self.html_basepath = html_basepath
        self.browser = None

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

    # Open an url in web browser
    def openUrl(self, url):
        try:
            self.getBrowser().set_page_load_timeout(self.load_timeout)
            self.getBrowser().get(url)
        except TimeoutException:
            logging.warning("Timeout exception during page load. Try to continue.")
        except:
            logging.error("Unexpected exception during page load. Exiting.")
            raise
        else:
            logging.debug("browser.get() returned without exceptions")

    def genHTMLFilePath(self, endpoint):
        return os.path.join(self.html_basepath, self.company_id + self.htmlfile_suffix[endpoint] + ".html")

    def writeHTMLFile(self, html, endpoint):
        htmlfile = self.genHTMLFilePath(endpoint)
        logging.info("Writing " + str(endpoint) + " in " + htmlfile)
        with open(htmlfile, 'w', encoding='utf-8') as fileh:
            fileh.write(html)

    # Get saved HTML code
    def getHTMLFile(self, endpoint):
        if endpoint not in self.htmlfile_suffix:
            raise RuntimeError("The endpoint you passed is not mapped anywhere")
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
                if (cbscraper.common.wasRobotDetected(filecont)):
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
    def waitForPresence(self, by, value):
        if self.is404():
            return False
        
        if True:
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
                logging.debug("Page element correctly found")
        
        #Post-loading sleep
        self.randSleep(self.postload_sleep_min, self.postload_sleep_max)

    def makeSoupFromHTML(self, html):
        return bs.BeautifulSoup(html, 'lxml')

    def makeAllSoup(self):
        for endpoint in OrgEndPoint:
            soup = self.getEndpointSoup(endpoint)
            if soup is False:
                html = self.getEndpointHTML(endpoint)
                if html is False:
                    soup = self.getEndpointSoup(OrgEndPoint.ENTITY)
                else:
                    soup = self.makeSoupFromHTML(html)
                self.setEndpointSoup(endpoint, soup)

    # Browser functions
    def getBrowser(self):
        if self.browser is None:
            self.browser = cbscraper.common.getWebDriver()
        return self.browser

    #Get HTML source code of a webpage and handle robot detection
    def getBrowserPageSource(self, curr_endpoint=None):
        html = self.getBrowser().page_source
        if (cbscraper.common.wasRobotDetected(html)):
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

    # Getters / Setters for HTML
    def getEndpointHTML(self, endpoint):
        return self.endpoint_html[endpoint]

    def setEndpointHTML(self, endpoint, html):
        self.endpoint_html[endpoint] = html

    # Getterss/Setters for soup
    def getEndpointSoup(self, endpoint):
        return self.endpoint_soup[endpoint]

    def setEndpointSoup(self, endpoint, soup):
        self.endpoint_soup[endpoint] = soup
        
    ############################################
        # ORGANIZATION SPECIFIC METHODS #  
    ############################################
    
    # Have the browser go to the page of the 'entity' ednpoint (overview page)
    def goToEntityPage(self):
        if self.entity_page:
            logging.info("Already on entity page")
            pass
        elif self.prev_page_is_entity:
            logging.info("Going back to entity page")
            self.getBrowser().back()
            self.randSleep(self.back_sleep_min, self.back_sleep_max)
        else:
            logging.info("Opening entity page")
            self.openUrl(self.cb_organization_url + self.company_id)
        self.entity_page = True
        self.prev_page_is_entity = False
        
    # Get link located in the organization 'entity' page
    def getBrowserLink(self, endpoint):
        return self.getBrowser().find_element_by_xpath('//a[@title="' + self.link_map[endpoint] + '"]')

    # If the organization entity page has a link for more of the information in 'endpoint', return that link
    def isMore(self, endpoint):
        return self.getEndpointSoup(OrgEndPoint.ENTITY).find('a', attrs={'title': self.link_map[endpoint]})

    # Scrape an organization
    def scrape(self):
        logging.info("Start scraping " + self.company_id)
        self.entity_page = False
        self.prev_page_is_entity = False
        # Get endpoint 'entity'
        endpoint = OrgEndPoint.ENTITY
        entity_html = self.getHTMLFile(endpoint)
        if entity_html is False:
            self.goToEntityPage()
            self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
            entity_html = self.getBrowserPageSource(endpoint)
        self.setEndpointHTML(OrgEndPoint.ENTITY, entity_html)
        entity_soup = self.makeSoupFromHTML(entity_html)
        self.setEndpointSoup(OrgEndPoint.ENTITY, entity_soup)
        # Process endpoints other than the entity one
        for endpoint in OrgEndPoint:
            if (endpoint is not OrgEndPoint.ENTITY) and self.isMore(endpoint):
                logging.info("More of " + str(endpoint) + " found")
                html = self.getHTMLFile(endpoint)
                if not html:
                    self.goToEntityPage()
                    link = self.getBrowserLink(endpoint)
                    logging.info("Clicking on '" + link.get_attribute('title') + "' link")
                    self.clickLink(link)
                    self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
                    self.entity_page = False
                    self.prev_page_is_entity = True
                    html = self.getBrowserPageSource(endpoint)
                self.setEndpointHTML(endpoint, html)
        # Make the soup of downloaded HTML pages
        self.makeAllSoup()