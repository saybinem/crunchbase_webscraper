import logging
from enum import Enum

from selenium.webdriver.common.by import By

import cbscraper.GenericScraper


class OrgEndPoint(Enum):
    ENTITY = 'entity'
    PEOPLE = 'people'
    ADVISORS = 'advisors'
    PAST_PEOPLE = 'past_people'


class CompanyScraper(cbscraper.GenericScraper.GenericScraper):
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

    def __init__(self, company_id, html_basepath):
        super().__init__()
        self.company_id = company_id
        self.html_basepath = html_basepath

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
