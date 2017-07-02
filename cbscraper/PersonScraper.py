import logging
from enum import Enum

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import cbscraper.GenericScraper


class PersonEndPoint(Enum):
    ENTITY =  1
    INVESTMENTS = 2


class PersonScraper(cbscraper.GenericScraper.GenericScraper):

    html_basepath = './data/person/html'

    # Name of the class to wait for when we load a page
    class_wait = {
        PersonEndPoint.ENTITY: 'entity',
        PersonEndPoint.INVESTMENTS: 'investments'
    }

    # Suffixes of HTML files
    htmlfile_suffix = {
        PersonEndPoint.ENTITY : '',
        PersonEndPoint.INVESTMENTS : '_investments'
    }

    # Title attribute of the link tags in the organization 'entity' page
    link_map = {
        PersonEndPoint.INVESTMENTS : 'All Investments'
    }

    cb_url = "https://www.crunchbase.com/person/"

    # Have the browser go to the page of the 'entity' ednpoint (overview page)
    def goToEntityPage(self):
        if self.entity_page:
            logging.info("Already on entity page")
            pass
        elif self.prev_page_is_entity:
            logging.info("Going back to entity page")
            try:
                self.getBrowser().back()
            except TimeoutException:
                logging.warning("Timeout exception during back(). Try to continue.")
            except:
                logging.critical("Unhandled exception during back. Exitin.")
                exit()
            self.randSleep(self.back_sleep_min, self.back_sleep_max)
        else:
            logging.info("Opening entity page")
            self.openUrl(self.cb_url + self.id)
        self.entity_page = True
        self.prev_page_is_entity = False

    # Scrape an organization
    def scrape(self):
        logging.info("Start scraping " + self.id)
        self.entity_page = False
        self.prev_page_is_entity = False

        # Get endpoint 'entity'
        endpoint = PersonEndPoint.ENTITY
        entity_html = self.getHTMLFile(endpoint)
        if entity_html is False:
            self.goToEntityPage()
            self.waitForPresence(By.CLASS_NAME, self.class_wait[endpoint])
            entity_html = self.getBrowserPageSource(endpoint)
        self.setEndpointHTML(PersonEndPoint.ENTITY, entity_html)
        entity_soup = self.makeSoupFromHTML(entity_html)
        self.setEndpointSoup(PersonEndPoint.ENTITY, entity_soup)

        # Process endpoints other than the entity one
        for endpoint in self.link_map.keys():
            if self.isMore(PersonEndPoint.ENTITY,endpoint):
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
        for endpoint in PersonEndPoint:
            soup = self.getEndpointSoup(endpoint)
            if soup is False:
                html = self.getEndpointHTML(endpoint)
                if html is False:
                    soup = self.getEndpointSoup(PersonEndPoint.ENTITY)
                else:
                    soup = self.makeSoupFromHTML(html)
                self.setEndpointSoup(endpoint, soup)
