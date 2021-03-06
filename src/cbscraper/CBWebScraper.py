import logging
from abc import abstractmethod

from cbscraper.GenericWebScraper import EBrowser
import cbscraper.GenericWebScraper
from selenium.common.exceptions import NoSuchElementException


class CBWebScraper(cbscraper.GenericWebScraper.GenericWebScraper):

    postload_sleep_min = 10  # Time to wait after the successful location of an element. Used in waitForPresenceCondition()
    postload_sleep_max = 20

    browser_type = EBrowser.FIREFOX
    is_firefox_user_profile = True

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
    @staticmethod
    def is404(soup):
        return soup.find('div', id='error-404') is not None

    # ROBOT detection
    def wasRobotDetected(self, soup):
        html_code = str(soup).lower()
        if ("robots" in html_code and "noindex, nofollow" in html_code):
            logging.error("Robot detected by test 1")
            return True
        if 'Pardon Our Interruption...' in html_code:
            logging.error("Robot detected by test 2")
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
