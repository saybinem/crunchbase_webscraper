import codecs
import json
import logging
import os
import time
import random
import bs4 as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Global vriables
browser = None
browser_quit = True #if True, quit the browser after retrieving the page. This may mitigate problem of robot detection

def myTextStrip(str):
    return str.replace('\n', '').strip()


def jsonPretty(dict_data):
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '))


# check robots
def wasRobotDetected(content):
    if (content.find('"ROBOTS"') >= 0 and content.find('"NOINDEX, NOFOLLOW"') >= 0):
        logging.warning("Robot detected by test 1")
        return True

    if (content.find('"robots"') >= 0 and content.find('"noindex, nofollow"') >= 0):
        logging.warning("Robot detected by test 2")
        return True

    if (content.find('Pardon Our Interruption...') >= 0):
        logging.warning("Robot detected by test 3")
        return True

    return False


# Requesting page with random delay and custom headers
def getPageSourceCode(url, by_condition, by_value):
    global browser

    # Use selenium
    logging.info("\t[getPageSourceCode] Running Selenium")

    if (browser is None):
        # Chrome
        chrome_profile = r"C:\Users\raffa\AppData\Local\Google\Chrome\User Data"
        chrome_driver = r"C:\data\bin\chromedriver.exe"
        options = webdriver.ChromeOptions()
        options.add_argument("user-data-dir=" + chrome_profile)  # Path to your chrome profile
        #options.add_argument("--incognito") #run in incognito mode
        options.add_argument("--start-maximized")
        #browser = webdriver.Chrome(executable_path=chrome_driver, chrome_options=options)

        # Firefox (user profile)
        #profile_path = r"C:\Users\raffa\AppData\Roaming\Mozilla\Firefox\Profiles\4ai6x5sv.default"
        #profile = webdriver.FirefoxProfile()
        #browser = webdriver.Firefox(firefox_profile=profile)

        #Firefox new profile
        browser = webdriver.Firefox()

    # Sleep to avoid robots
    sec = random.randint(5, 20)
    logging.info("Sleeping for " + str(sec) + " to avoid robot detection...")
    time.sleep(sec)

    # Get page
    try:
        browser.set_page_load_timeout(30)
        browser.get(url)
    except TimeoutException:
        logging.warning("Timeout exception during page load. Try to continue.")
        pass
    except:
        logging.error("Unexpected exception during page load. Exiting.")
        raise
    else:
        logging.debug("browser.get() returned without exceptions")

    # Sleep to avoid robots
    sec = 20
    logging.info("post loading sleep for " + str(sec))
    time.sleep(sec)

    # Wait until condition occur
    #if by_condition is not None:
    if False:
        timeout = 30  # seconds
        try:
            by = ''
            if by_condition == 'class_name':
                by = By.CLASS_NAME
            elif by_condition == 'xpath':
                by = By.XPATH
            elif by_condition == 'id':
                by = By.ID
            else:
                logging.error("By condition is not valid")
                exit()

            condition_str = "("+by+","+by_value+")"
            logging.info("Waiting for presence of " + condition_str)
            condition = EC.presence_of_element_located((by, by_value))
            WebDriverWait(browser, timeout).until(condition)
        except TimeoutException:
            logging.error("Timed out waiting for page element "+condition_str+". Exiting")
            raise
        except:
            logging.error("Unexpected exception waiting for page element "+condition_str+". Exiting")
            raise
        else:
            logging.debug("Page element "+condition_str+" found")

    # Get page source code and return it
    cont = browser.page_source
    if browser_quit:
        browser.quit()
    return cont


# Get a webpage and save to file (avoid another request). Return the page soup
def getPageSoup(url, filepath, by_condition, by_value):
    # Check if HTML file already exist
    if os.path.isfile(filepath):

        # Check if we can read from the file
        with codecs.open(filepath, 'r', 'utf-8') as fileh:
            try:
                filecont = fileh.read()
            except UnicodeDecodeError:
                logging.error("UnicodeDecodeError on " + filepath + " redownloading it...")
                fileh.close()
                os.unlink(filepath)
                filecont = ''

        # Check if the page served was the one for robots
        if filecont != '':
            if (wasRobotDetected(filecont)):
                logging.warning("\t[getPageSoup] Pre-saved file contains robot. Removing it...")
                os.unlink(filepath)
            else:
                logging.info("\t[getPageSoup] Returning content from pre-saved file " + filepath)
                soup = bs.BeautifulSoup(filecont, 'lxml')
                return soup

    # Get actual source code
    logging.info("\t[getPageSoup] calling getPageSourceCode( " + url + ")")
    cont = getPageSourceCode(url, by_condition, by_value)

    # Get the soup
    # print("type(cont): "+str(type(cont)))
    soup = bs.BeautifulSoup(cont, 'lxml')

    # Save HTML code in file
    with codecs.open(filepath, 'w', 'utf-8') as fileh:
        fileh.write(cont)

    # Check for robot detection
    if wasRobotDetected(cont):
        logging.error("\t[getPageSoup] ROBOT: I have downloaded a file that contains robot detection: " + filepath)
        exit()
    else:
        logging.debug("\t[getPageSoup] File downloaded successfully")
        return soup
