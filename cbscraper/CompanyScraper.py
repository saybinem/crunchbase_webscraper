import logging
import os
import random
import time
from enum import Enum

import bs4 as bs
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class CBEndpoint(Enum):
    ORG_ENTITY = 'entity'
    ORG_PEOPLE = 'people'
    ORG_ADVISORS = 'advisors'
    ORG_PAST_PEOPLE = 'past_people'


class CompanyScraper():
    postload_sleep_min = 5
    postload_sleep_max = 15

    load_timeout = 30
    wait_timeout = 60

    class_wait = {
        CBEndpoint.ORG_ENTITY: 'entity',
        CBEndpoint.ORG_PAST_PEOPLE: 'past_people',
        CBEndpoint.ORG_PEOPLE: 'people',
        CBEndpoint.ORG_ADVISORS: 'advisors',
    }

    htmlfile_suffix = {
        CBEndpoint.ORG_ENTITY: '_overview',
        CBEndpoint.ORG_PEOPLE: '_people',
        CBEndpoint.ORG_ADVISORS: '_board',
        CBEndpoint.ORG_PAST_PEOPLE: '_past_people',
    }

    html_entity = False
    html_currteam = False
    html_pastteam = False
    html_adv = False

    # last / is included
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

    def openUrl(self, url):
        # Get page
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

    def getHtmlFile(self, endpoint):
        if endpoint not in self.htmlfile_suffix:
            raise RuntimeError("The endpoint you passed is not mapped anywhere")
        htmlfile = os.path.join(self.html_basepath, self.company_id + self.htmlfile_suffix[endpoint] + ".html")
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
                if (wasRobotDetected(filecont)):
                    logging.warning("Pre-saved file contains robot. Removing it...")
                    os.unlink(htmlfile)
                    return False
                else:
                    logging.debug("Returning content from pre-saved file " + htmlfile)
                    return filecont
        else:
            logging.debug("HTML file " + htmlfile + " not found")
            return False

    def waitForPresence(self, by, value):
        try:
            logging.info("Waiting for presence of (" + str(by) + "," + value + ")")
            condition = EC.presence_of_element_located((by, value))
            WebDriverWait(self.getBrowser(), self.wait_timeout).until(condition)
        except TimeoutException:
            logging.error("Timed out waiting for page element.")
            pass
        except:
            logging.error("Unexpected exception waiting for page element. Exiting")
            raise
        else:
            logging.critical("Page element found")
        self.postLoad()
        
    # Have the browser go to the page relative to endpoint 'entity' (overview page)
    def goToEntityPage(self):
        if self.entity_page:
            logging.info("Already on entity page")
            pass
        elif self.prev_page_is_entity:
            logging.info("Going back to entity page")
            self.getBrowser().back()
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

    # Get links from browser
    def getLinkCurrentTeam(self):
        return self.getBrowser().find_element_by_xpath('//a[@title="All Current Team"]')

    def getLinkPastTeam(self):
        return self.getBrowser().find_element_by_xpath('//a[@title="All Past Team"]')

    def getLinkAdvisors(self):
        return self.getBrowser().find_element_by_xpath('//a[@title="All Board Members and Advisors"]')

    # Get if we have additional sections
    def isCurrentTeam(self):
        return self.getEntitySoup().find('a', attrs={'title': 'All Current Team'})

    def isPastTeam(self):
        return self.getEntitySoup().find('a', attrs={'title': 'All Past Team'})

    def isAdvisors(self):
        return self.getEntitySoup().find('a', attrs={'title': 'All Board Members and Advisors'})

    def getBrowser(self):
        if self.browser is None:
            self.browser = getWebDriver()
        return self.browser

    def getBrowserPageSource(self):
        return self.getBrowser().page_source

    # called when we finish loading a page
    def postLoad(self):
        self.randSleep(self.postload_sleep_min, self.postload_sleep_max)

    # Scrape an organization
    def scrape(self):

        logging.info("Start scraping " + self.company_id)

        self.entity_page = False
        self.prev_page_is_entity = False

        # Get endpoint 'entity'
        html_entity = self.getHtmlFile(CBEndpoint.ORG_ENTITY)
        if html_entity is False:
            self.goToEntityPage()
            html_entity = self.getBrowserPageSource()

        self.setEntityHTML(html_entity)
        self.setEntitySoup(self.makeSoupFromHTML(self.getEntityHTML()))

        # Get current team
        if self.isCurrentTeam():
            endpoint = CBEndpoint.ORG_PEOPLE
            logging.info("More " + str(endpoint) + " found")
            html = self.getHtmlFile(endpoint)
            if not html:
                self.goToEntityPage()
                link = self.getLinkCurrentTeam()
                logging.info("Clicking on current team link")
                link.click()
                self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
                self.entity_page = False
                self.prev_page_is_entity = True
                html = self.getBrowserPageSource()
            self.setCurrTeamHTML(html)

        # Get past team
        if self.isPastTeam():
            endpoint = CBEndpoint.ORG_PAST_PEOPLE
            logging.info("More " + str(endpoint) + " found")
            html = self.getHtmlFile(endpoint)
            if not html:
                self.goToEntityPage()
                link = self.getLinkPastTeam()
                logging.info("Clicking on past team link")
                link.click()
                self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
                self.entity_page = False
                self.prev_page_is_entity = True
                html = self.getBrowserPageSource()
            self.setPastTeamHTML(html)

        # Get advisors
        if self.isAdvisors():
            endpoint = CBEndpoint.ORG_ADVISORS
            logging.info("More " + str(endpoint) + " found")
            html = self.getHtmlFile(endpoint)
            if not html:
                self.goToEntityPage()
                link = self.getLinkAdvisors()
                logging.info("Clicking on advisors link")
                link.click()
                self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
                self.entity_page = False
                self.prev_page_is_entity = True
                html = self.getBrowserPageSource()
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
