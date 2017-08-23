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
    screenshot_basepath = cbscraper.global_vars.company_screens_dir

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
            # We cannot have 404 error here.
            # This is a page that follows the entity page (e.g. the past_people page)
            # If the entity page is a 404 page, we couldn't have got to this point
            self.waitForClass(OrgEndPoint.ENTITY)
        else:
            logging.debug("Opening entity page")
            self.openURL(self.cb_url + self.id)
            try:
                html = self.getBrowserPageSource()
                soup = self.makeSoupFromHTML(html)
                if self.is404(soup):
                    raise Error404
                self.waitForClass(OrgEndPoint.ENTITY)
            except selenium.common.exceptions.TimeoutException:
                logging.error("Timeout exception. Retry")
                return self.goToEntityPage()
        self.entity_page = True
        self.prev_page_is_entity = False

    # Get endpoint 'Entity' from a saved HTML file
    def getEntityEndpointFromHTMLFile(self):
        entity_html = self.getHTMLFile(OrgEndPoint.ENTITY)
        if entity_html:
            entity_soup = self.makeSoupFromHTML(entity_html)
            is404 = self.is404(entity_soup)
            if is404:
                logging.info("HTML file contains error 404")
                raise Error404
            robot = self.wasRobotDetected(entity_soup)
            if robot:
                logging.info("HTML file contains robot detection. Re-download")
                os.unlink(self.genHTMLFilePath(OrgEndPoint.ENTITY))
            else:
                logging.debug("Content retrieved from HTML file")
        else:
            logging.debug("No HTML file")
        return entity_html

    # Scrape an organization
    def scrape(self):
        logging.debug("Start scraping " + self.id)
        self.entity_page = False
        self.prev_page_is_entity = False

        # Get endpoint 'entity'
        entity_html = self.getEntityEndpointFromHTMLFile()

        if not entity_html:
            try:
                self.goToEntityPage()
                self.randSleep(self.postload_sleep_min, self.postload_sleep_max)
            except Error404:
                logging.error("Caught error 404. Re-raising")
                raise
            finally:
                # Write HTML to file and get screenshot even if we get a 404 error
                entity_html = self.getBrowserPageSource()
                self.writeHTMLFile(entity_html, OrgEndPoint.ENTITY)
                self.saveScreenshotEndpoint(OrgEndPoint.ENTITY)

        # Set endpoint 'entity''s HTML and soup
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
                    self.randSleep(self.postload_sleep_min, self.postload_sleep_max)
                    link = self.getBrowserLink(endpoint)
                    logging.info("Clicking on '" + link.get_attribute('title') + "' link")
                    self.clickLink(link)
                    self.randSleep(self.postload_sleep_min, self.postload_sleep_max)
                    # No need to check for 404 since we obtained the link from the webpage
                    self.waitForClass(endpoint)
                    self.entity_page = False
                    self.prev_page_is_entity = True
                    html = self.getBrowserPageSource()
                    self.writeHTMLFile(html, endpoint)
                    self.saveScreenshotEndpoint(endpoint)
                self.setEndpointHTML(endpoint, html)
        # Make the soup of downloaded HTML pages
        self.makeAllSoup()
        logging.debug("Returning True")
        return True

    def makeAllSoup(self):
        """
        Make the soup for all endpoints
        If an endpoint is missing, its soup is set equal to the 'entity' endpoint soup, which acts as a fallback
        :return:
        """
        for endpoint in OrgEndPoint:
            soup = self.getEndpointSoup(endpoint)
            if soup is False:
                html = self.getEndpointHTML(endpoint)
                if html is False:
                    soup = self.getEndpointSoup(OrgEndPoint.ENTITY)
                else:
                    soup = self.makeSoupFromHTML(html)
                self.setEndpointSoup(endpoint, soup)
