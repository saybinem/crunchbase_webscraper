import logging
from enum import Enum
import os

import cbscraper.CrunchbaseScraper
import cbscraper.GenericScraper
from cbscraper.GenericScraper import Error404

class OrgEndPoint(Enum):
    ENTITY = 1
    PEOPLE = 2
    ADVISORS = 3
    PAST_PEOPLE = 4


class CompanyScraper(cbscraper.CrunchbaseScraper.CrunchbaseScraper):

    html_basepath = './data/company/html'
    screenshot_folder = './data/company/screenshots'

    class_wait = {
        OrgEndPoint.ENTITY: 'entity',
        OrgEndPoint.PAST_PEOPLE: 'past_people',
        OrgEndPoint.PEOPLE: 'people',
        OrgEndPoint.ADVISORS: 'advisors',
    }

    htmlfile_suffix = {
        OrgEndPoint.ENTITY : '_overview',
        OrgEndPoint.PEOPLE : '_people',
        OrgEndPoint.ADVISORS : '_board',
        OrgEndPoint.PAST_PEOPLE : '_past_people',
    }

    link_map = {
        OrgEndPoint.PEOPLE : 'All Current Team',
        OrgEndPoint.ADVISORS : 'All Board Members and Advisors',
        OrgEndPoint.PAST_PEOPLE : 'All Past Team'
    }

    #CB starting URL
    cb_url = "https://www.crunchbase.com/organization/"
    
    # Have the browser go to the page of the 'entity' endpoint (overview page)
    def goToEntityPage(self):
        if self.entity_page:
            logging.debug("Already on entity page")
            pass
        elif self.prev_page_is_entity:
            logging.debug("Going back to entity page")
            self.goBack()
            self.waitForClass(OrgEndPoint.ENTITY)
        else:
            logging.debug("Opening entity page")
            self.openURL(self.cb_url + self.id)
            self.waitForClass(OrgEndPoint.ENTITY)
        self.entity_page = True
        self.prev_page_is_entity = False

    # Scrape an organization
    def scrape(self):
        logging.debug("Start scraping " + self.id)
        self.entity_page = False
        self.prev_page_is_entity = False

        # Get endpoint 'entity'
        endpoint = OrgEndPoint.ENTITY
        entity_html = False

        try:
            entity_html = self.getHTMLFile(endpoint)
        except Error404 as e:
            logging.debug("Detected 404 in HTML file")
            raise
        else:
            if not entity_html:
                try:
                    self.goToEntityPage()
                except cbscraper.GenericScraper.Error404:
                    logging.error("Caught error 404. Returning False")
                    return False
                finally:
                    # Write HTML to file and get screenshot even if we get a 404 error
                    entity_html = self.getBrowserPageSource(endpoint)
                    self.saveScreenshot(os.path.join(self.screenshot_folder, self.id + ".png"))
            else:
                logging.debug("Content retrieved from HTML file")

        # Make the soup
        self.setEndpointHTML(OrgEndPoint.ENTITY, entity_html)
        entity_soup = self.makeSoupFromHTML(entity_html)
        self.setEndpointSoup(OrgEndPoint.ENTITY, entity_soup)

        # Process endpoints other than the entity one
        for endpoint in self.link_map.keys():
            if self.isMore(OrgEndPoint.ENTITY, endpoint):
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
        logging.debug("Returning True")
        return True

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
