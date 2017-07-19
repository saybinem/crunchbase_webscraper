import logging
from enum import Enum

import cbscraper.CrunchbaseScraper
import cbscraper.GenericScraper
from cbscraper.GenericScraper import Error404
import os
from selenium.webdriver.common.by import By

class PersonEndPoint(Enum):
    ENTITY = 1
    INVESTMENTS = 2


class PersonScraper(cbscraper.CrunchbaseScraper.CrunchbaseScraper):
    html_basepath = './data/person/html'
    screenshot_folder = './data/person/screenshots'

    # Name of the class to wait for when we load a page
    class_wait = {
        PersonEndPoint.ENTITY : 'entity',
        PersonEndPoint.INVESTMENTS : 'investments'
    }

    # Suffixes of HTML files
    htmlfile_suffix = {
        PersonEndPoint.ENTITY: '',
        PersonEndPoint.INVESTMENTS : '_investments'
    }

    # Title attribute of the link tags in the organization 'entity' page
    link_map = {
        PersonEndPoint.INVESTMENTS : 'All Investments'
    }

    cb_url = "https://www.crunchbase.com/person/"

    def __init__(self, id):
        self.entity_page = False
        self.prev_page_is_entity = False
        super().__init__(id)

    def entityWait(self):
        self.waitForClass(PersonEndPoint.ENTITY)
        self.waitForPresenceCondition(By.ID, 'profile_header_heading', sleep=False)

    # Have the browser go to the page of the 'entity' ednpoint (overview page)
    def goToEntityPage(self):
        if self.entity_page:
            logging.debug("Already on entity page")
            return True
        elif self.prev_page_is_entity:
            logging.debug("Going back to entity page")
            self.goBack()
            try:
                self.entityWait()
            except Error404:
                logging.debug("Error 404")
                raise
            except:
                logging.critical("Unhandled exception")
                raise
            else:
                self.entity_page = True
                self.prev_page_is_entity = False
                return True
        else:
            logging.debug("Opening entity page")
            self.openURL(self.cb_url + self.id)
            try:
                self.entityWait()
            except Error404:
                logging.debug("Error 404")
                raise
            except:
                logging.critical("Unhandled exception")
                raise
            else:
                self.entity_page = True
                self.prev_page_is_entity = False
                return True

    # Scrape an organization
    def scrape(self):
        #logging.info("Start scraping " + self.id)

        # Get endpoint 'entity'
        endpoint = PersonEndPoint.ENTITY
        entity_html = False
        #try to get it from file
        try:
            entity_html = self.getHTMLFile(endpoint)
        except Error404 as e:
            logging.debug("HTML file contain 404 error")
            raise

        #try to get it from the web
        if entity_html is False:
            try:
                self.goToEntityPage()
            except Error404 as e:
                logging.debug("Page contain 404 error")
                raise
            finally:
                # SAVE HTML TO FILE (EVEN IF WE HAVE A 404 ERROR)
                entity_html = self.getBrowserPageSource(endpoint)
                self.saveScreenshot(os.path.join(self.screenshot_folder, self.id + ".png"))
            
        self.setEndpointHTML(PersonEndPoint.ENTITY, entity_html)
        entity_soup = self.makeSoupFromHTML(entity_html)
        self.setEndpointSoup(PersonEndPoint.ENTITY, entity_soup)

        # Process endpoints other than the entity one
        for endpoint in self.link_map.keys():
            if self.isMore(PersonEndPoint.ENTITY, endpoint):
                logging.debug("More of " + str(endpoint) + " found")
                html = self.getHTMLFile(endpoint)
                if not html:
                    self.goToEntityPage()
                    link = self.getBrowserLink(endpoint)
                    logging.info("Clicking on '" + link.get_attribute('title') + "' link")
                    self.clickLink(link)
                    self.waitForClass(endpoint)
                    self.entity_page = False
                    self.prev_page_is_entity = True
                    html = self.getBrowserPageSource(endpoint)
                self.setEndpointHTML(endpoint, html)
        # Make the soup of downloaded HTML pages
        self.makeAllSoup()
        return True

    def makeAllSoup(self):
        for endpoint in PersonEndPoint:
            soup = self.getEndpointSoup(endpoint)
            if soup is False:
                html = self.getEndpointHTML(endpoint)
                if html is False:
                    soup = self.getEndpointSoup(PersonEndPoint.ENTITY)
                else:
                    soup = self.makeSoupFromHTML(html)
                self.setEndpointSoup(endpoint, soup)

    @property
    def soup_entity(self):
        return self.getEndpointSoup(PersonEndPoint.ENTITY)

    @property
    def soup_inv(self):
        return self.getEndpointSoup(PersonEndPoint.INVESTMENTS)

    @soup_entity.setter
    def soup_entity(self, value):
        self.setEndpointSoup(PersonEndPoint.ENTITY, value)
