import logging
from enum import Enum
import os

import cbscraper.CBWebScraper
import cbscraper.GenericWebScraper
from cbscraper.GenericWebScraper import Error404
import selenium.common.exceptions
import cbscraper.global_vars

class OrgEndPoint(Enum):
    ENTITY = 1
    PEOPLE = 2
    ADVISORS = 3
    PAST_PEOPLE = 4


class CBCompanyWebScraper(cbscraper.CBWebScraper.CBWebScraper):

    html_basepath = cbscraper.global_vars.company_html_dir
    screenshot_folder = cbscraper.global_vars.company_screens_dir

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
            try:
                self.waitForClass(OrgEndPoint.ENTITY)
            except selenium.common.exceptions.TimeoutException:
                logging.error("Timeout exception. Retry")
                return self.goToEntityPage()
        self.entity_page = True
        self.prev_page_is_entity = False

    # Scrape an organization
    def scrape(self):
        logging.debug("Start scraping " + self.id)
        self.entity_page = False
        self.prev_page_is_entity = False

        # Get endpoint 'entity'
        endpoint = OrgEndPoint.ENTITY
        entity_html = self.getHTMLFile(endpoint)
        if not entity_html:
            try:
                self.goToEntityPage()
            except cbscraper.GenericWebScraper.Error404:
                logging.error("Caught error 404. Re-raising")
                raise
            finally:
                # Write HTML to file and get screenshot even if we get a 404 error
                entity_html = self.getBrowserPageSource(endpoint)
                self.saveScreenshot(os.path.join(self.screenshot_folder, self.id + ".png"))
        else:
            entity_soup = self.makeSoupFromHTML(entity_html)
            is404 = self.is404(entity_soup)
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
