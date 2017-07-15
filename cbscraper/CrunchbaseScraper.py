import logging
from abc import abstractmethod

from cbscraper.GenericScraper import EBrowser
import cbscraper.GenericScraper
from selenium.common.exceptions import NoSuchElementException


class CrunchbaseScraper(cbscraper.GenericScraper.GenericScraper):

    browser_type = EBrowser.PHANTOMJS
    is_firefox_user_profile = True
    screenshot_folder = ''    
    
    # map an endpoint to an <a> tag title attribute
    @property
    @abstractmethod
    def link_map(self):
        pass

    # Get link located in the organization 'entity' page
    def getBrowserLink(self, endpoint):
        return self.getBrowser().find_element_by_xpath('//a[@title="' + self.link_map[endpoint] + '"]')

    # If the organization entity page has a link for more of the information in 'endpoint', return that link
    def isMore(self, start_point, link_point):
        return self.getEndpointSoup(start_point).find('a', attrs={'title': self.link_map[link_point]})

    # return false if we obtained a missing link
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

    # ROBOT detection
    def wasRobotDetected(self, hmtl_code):
        if (hmtl_code.find('"ROBOTS"') >= 0 and hmtl_code.find('"NOINDEX, NOFOLLOW"') >= 0):
            logging.error("Robot detected by test 1")
            return True
        if (hmtl_code.find('"robots"') >= 0 and hmtl_code.find('"noindex, nofollow"') >= 0):
            logging.error("Robot detected by test 2")
            return True
        if (hmtl_code.find('Pardon Our Interruption...') >= 0):
            logging.error("Robot detected by test 3")
            return True
        return False

    def detectedAsRobot(self):
        logging.info("We were detected as robots. Refreshing the page")
        self.browserRefresh()
        self.randSleep(10, 15)
        detected = self.wasRobotDetected(self.getBrowserPageSource())
        if not detected:
            logging.info("Detection escaped")
            return True

        logging.info("We are still being detected. Restarting the browser")
        self.sendRobotEmail()
        url = self.getBrowserURL()
        self.restartBrowser()
        self.randSleep(self.wait_robot_min, self.wait_robot_max)
        self.openURL(url)
        detected = self.wasRobotDetected(self.getBrowserPageSource())
        if not detected:
            logging.info("Detection escaped")
            return True
        return self.detectedAsRobot()
