import logging
import os
import random
import time
from enum import Enum

import cbscraper.common

import bs4 as bs
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class CBEndpoint(Enum):
    ORG_ENTITY = 'entity'
    ORG_PEOPLE = 'people'
    ORG_ADVISORS = 'advisors'
    ORG_PAST_PEOPLE = 'past_people'


class CompanyScraper():

    postload_sleep_min = 2
    postload_sleep_max = 10

    back_sleep_min = 2
    back_sleep_max = 6

    load_timeout = 30
    wait_timeout = 60

    #Name of the class to wait for when we load a page
    class_wait = {
        CBEndpoint.ORG_ENTITY: 'entity',
        CBEndpoint.ORG_PAST_PEOPLE: 'past_people',
        CBEndpoint.ORG_PEOPLE: 'people',
        CBEndpoint.ORG_ADVISORS: 'advisors',
    }

    #Suffixes of HTML files
    htmlfile_suffix = {
        CBEndpoint.ORG_ENTITY: '_overview',
        CBEndpoint.ORG_PEOPLE: '_people',
        CBEndpoint.ORG_ADVISORS: '_board',
        CBEndpoint.ORG_PAST_PEOPLE: '_past_people',
    }

    #Title attribute of the link tags in the organization 'entity' page
    link_map = {
        CBEndpoint.ORG_PEOPLE : 'All Current Team',
        CBEndpoint.ORG_ADVISORS: 'All Board Members and Advisors',
        CBEndpoint.ORG_PAST_PEOPLE : 'All Past Team'
    }

    html_entity = False
    html_currteam = False
    html_pastteam = False
    html_adv = False

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

    #return false if we btained a missing link
    def is404(self, html=None):
        if html is None:
            try:
                self.getBrowser().find_element_by_id('error-404')
            except NoSuchElementException:
                return False
            except:
                logging.critical("unexpected exception in is404()")
                raise
            else:
                return True
        else:
            soup=self.makeSoupFromHTML(html)
            return soup.find('div',id='error-404') is not None

    #Open an url in web browser
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
        logging.info("Writing "+str(endpoint) + " in " + htmlfile)
        with open(htmlfile, 'w', encoding='utf-8') as fileh:
            fileh.write(html)

    #Get saved HTML code
    def getHTMLFile(self, endpoint):
        if endpoint not in self.htmlfile_suffix:
            raise RuntimeError("The endpoint you passed is not mapped anywhere")
        htmlfile = self.genHTMLFilePath(endpoint)
        # Check if HTML file already exist
        if os.path.isfile(htmlfile):
            # Check if we can read from the file
            with open(htmlfile, 'r', encoding='utf-8') as fileh:
                try:
                    filecont = fileh.read()
                except UnicodeDecodeError:
                    logging.error("UnicodeDecodeError on " + htmlfile + ". Re-downloading it...")
                    fileh.close()
                    os.unlink(htmlfile)
                    return False
            # Check if the page served was the one for robots
            if filecont != '':
                if (cbscraper.common.wasRobotDetected(filecont)):
                    logging.warning("Pre-saved file contains robot. Removing it...")
                    os.unlink(htmlfile)
                    return False
                elif self.is404(filecont):
                    return False
                else:
                    logging.debug("Returning content from pre-saved file " + htmlfile)
                    return filecont
        else:
            logging.debug("HTML file " + htmlfile + " not found")
            return False

    # Check if there is 404 errore, Wait for the presence of an element in a web page and then wait for some more time
    def waitForPresence(self, by, value):

        if self.is404():
            return False

        try:
            logging.info("Waiting for presence of (" + str(by) + "," + value + "). URL="+self.getBrowser().current_url)
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
        self.randSleep(self.postload_sleep_min, self.postload_sleep_max)

    # Have the browser go to the page relative to endpoint 'entity' (overview page)
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

    def makeSoupFromHTML(self, html):
        return bs.BeautifulSoup(html, 'lxml')

    def makeAllSoup(self):
        # Current team
        html = self.getCurrTeamHTML()
        if html is False:
            self.setCurrTeamSoup(self.getEntitySoup())
        else:
            self.setCurrTeamSoup(self.makeSoupFromHTML(html))
        # Past team
        html = self.getPastTeamHTML()
        if html is False:
            self.setPastTeamSoup(self.getEntitySoup())
        else:
            self.setPastTeamSoup(self.makeSoupFromHTML(html))
        # Advisors
        html = self.getAdvisorsHTML()
        if html is False:
            self.setAdvisorsSoup(self.getEntitySoup())
        else:
            self.setAdvisorsSoup(self.makeSoupFromHTML(html))

    # Get link located in the organization 'entity' page
    def getBrowserLink(self, endpoint):
        return self.getBrowser().find_element_by_xpath('//a[@title="'+self.link_map[endpoint]+'"]')

    # Return if we have a specific page for that endpoint (only if there are a lot of information)
    def isMore(self, endpoint):
        return self.getEntitySoup().find('a', attrs={'title' : self.link_map[endpoint]})

    #Browser functions
    def getBrowser(self):
        if self.browser is None:
            self.browser = cbscraper.common.getWebDriver()
        return self.browser

    def getBrowserPageSource(self, curr_endpoint = None):
        html = self.getBrowser().page_source
        if curr_endpoint is not None:
            self.writeHTMLFile(html, curr_endpoint)
        return html

    # Scrape an organization
    def scrape(self):

        logging.info("Start scraping " + self.company_id)

        self.entity_page = False
        self.prev_page_is_entity = False

        # Get endpoint 'entity'
        endpoint = CBEndpoint.ORG_ENTITY
        html_entity = self.getHTMLFile(endpoint)
        if html_entity is False:
            self.goToEntityPage()
            self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
            html_entity = self.getBrowserPageSource(endpoint)

        self.setEntityHTML(html_entity)
        self.setEntitySoup(self.makeSoupFromHTML(self.getEntityHTML()))

        # Get current team
        endpoint = CBEndpoint.ORG_PEOPLE
        if self.isMore(endpoint):
            logging.info("More " + str(endpoint) + " found")
            html = self.getHTMLFile(endpoint)
            if not html:
                self.goToEntityPage()
                link = self.getBrowserLink(endpoint)
                logging.info("Clicking on current team link")
                link.click()
                self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
                self.entity_page = False
                self.prev_page_is_entity = True
                html = self.getBrowserPageSource(endpoint)
            self.setCurrTeamHTML(html)

        # Get past team
        endpoint = CBEndpoint.ORG_PAST_PEOPLE
        if self.isMore(endpoint):
            logging.info("More " + str(endpoint) + " found")
            html = self.getHTMLFile(endpoint)
            if not html:
                self.goToEntityPage()
                link = self.getBrowserLink(endpoint)
                logging.info("Clicking on past team link")
                link.click()
                self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
                self.entity_page = False
                self.prev_page_is_entity = True
                html = self.getBrowserPageSource(endpoint)
            self.setPastTeamHTML(html)

        # Get advisors
        endpoint = CBEndpoint.ORG_ADVISORS
        if self.isMore(endpoint):
            logging.info("More " + str(endpoint) + " found")
            html = self.getHTMLFile(endpoint)
            if not html:
                self.goToEntityPage()
                link = self.getBrowserLink(endpoint)
                logging.info("Clicking on advisors link")
                link.click()
                self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
                self.entity_page = False
                self.prev_page_is_entity = True
                html = self.getBrowserPageSource(endpoint)
            self.setAdvisorsHTML(html)

        # Make the soup of downloaded HTML pages
        self.makeAllSoup()

    # Getters / Setters for HTML
    def getEntityHTML(self):
        return self.html_entity

    def getCurrTeamHTML(self):
        return self.html_currteam

    def getPastTeamHTML(self):
        return self.html_pastteam

    def getAdvisorsHTML(self):
        return self.html_adv

    def setEntityHTML(self, html):
        self.html_entity = html

    def setCurrTeamHTML(self, html):
        self.html_currteam = html

    def setPastTeamHTML(self, html):
        self.html_pastteam = html

    def setAdvisorsHTML(self, html):
        self.html_adv = html

    # Getterss/Setters for soup
    def getEntitySoup(self):
        return self.soup_entity

    def getCurrTeamSoup(self):
        return self.soup_currteam

    def getPastTeamSoup(self):
        return self.soup_pastteam

    def getAdvisorsSoup(self):
        return self.soup_adv

    def setEntitySoup(self, soup):
        self.soup_entity = soup

    def setCurrTeamSoup(self, soup):
        self.soup_currteam = soup

    def setPastTeamSoup(self, soup):
        self.soup_pastteam = soup

    def setAdvisorsSoup(self, soup):
        self.soup_adv = soup
