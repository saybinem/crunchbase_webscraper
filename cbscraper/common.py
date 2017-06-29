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

# Non modifiable globals
browser = None
robot_errors = 0

# User global variables
browser_quit = False #if True, quit the browser after retrieving the page. This may mitigate problem of robot detection

pre_load_sleep_min = 0 #minimum number of seconds to wait before casking the webpage. Avoid robot detection
pre_load_sleep_max = 0

post_load_sleep_min = 20
post_load_sleep_max = 30

page_load_timeout = 60 #seconds before declaring that a page timed out
detected_wait_min = 240 #seconds to wait if we are detected as robots
detected_wait_max = 360

max_robot_errors = 3

def myTextStrip(str):
    return str.replace('\n', '').strip()


def jsonPretty(dict_data):
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '))


# check robots
def wasRobotDetected(content):
    logger = logging.getLogger("wasRobotDetected")

    if (content.find('"ROBOTS"') >= 0 and content.find('"NOINDEX, NOFOLLOW"') >= 0):
        logger.error("Robot detected by test 1")
        return True

    if (content.find('"robots"') >= 0 and content.find('"noindex, nofollow"') >= 0):
        logger.error("Robot detected by test 2")
        return True

    if (content.find('Pardon Our Interruption...') >= 0):
        logger.error("Robot detected by test 3")
        return True

    return False


# Requesting page with random delay and custom headers
def getPageSourceCode(url, by_condition, by_value):
    logger = logging.getLogger("getPageSourceCode")

    global browser

    if (browser is None):
        # Use selenium
        logger.debug("Creating webdriver")

        # Chrome
        #chrome_profile = r"C:\Users\raffa\AppData\Local\Google\Chrome\User Data"
        #chrome_driver = r"C:\data\bin\chromedriver.exe"
        #options = webdriver.ChromeOptions()
        #options.add_argument("user-data-dir=" + chrome_profile)  # Path to your chrome profile
        #options.add_argument("--incognito") #run in incognito mode
        #options.add_argument("--start-maximized")
        #browser = webdriver.Chrome(executable_path=chrome_driver, chrome_options=options)

        # Firefox (user profile)
        profile_path = r"C:\Users\raffa\AppData\Roaming\Mozilla\Firefox\Profiles\4ai6x5sv.default"
        profile = webdriver.FirefoxProfile(profile_path)
        browser = webdriver.Firefox(firefox_profile=profile)

        #Firefox new profile
        #browser = webdriver.Firefox()
        #browser.maximize_window()

    # Sleep to avoid robots
    sec = random.randint(pre_load_sleep_min, pre_load_sleep_max)
    logger.info("Pre-loading sleep of " + str(sec) + " seconds ...")
    time.sleep(sec)

    # Get page
    try:
        browser.set_page_load_timeout(page_load_timeout)
        browser.get(url)
    except TimeoutException:
        logger.warning("Timeout exception during page load. Try to continue.")
        pass
    except:
        logger.error("Unexpected exception during page load. Exiting.")
        raise
    else:
        logger.debug("browser.get() returned without exceptions")

    # Sleep to let the page load correctly
    # This is necessary because, to avoid robots, the page return immediately, although it is not yet gully loaded
    # Don't relay on page timeout
    sec = random.randint(post_load_sleep_min, post_load_sleep_max)
    logger.info("Post-loading sleep of " + str(sec) + " seconds...")
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
                logger.error("By condition is not valid")
                exit()

            condition_str = "("+by+","+by_value+")"
            logger.info("Waiting for presence of " + condition_str)
            condition = EC.presence_of_element_located((by, by_value))
            WebDriverWait(browser, timeout).until(condition)
        except TimeoutException:
            logger.error("Timed out waiting for page element "+condition_str+". Exiting")
            raise
        except:
            logger.error("Unexpected exception waiting for page element "+condition_str+". Exiting")
            raise
        else:
            logger.debug("Page element "+condition_str+" found")

    # Get page source code and return it
    cont = browser.page_source
    if browser_quit:
        browser.quit()
        browser = None
    return cont


# Get a webpage and save to file (avoid another request). Return the page soup
def getPageSoup(url, filepath, by_condition, by_value):
    global robot_errors

    logger = logging.getLogger("getPageSoup")

    # Check if HTML file already exist
    if os.path.isfile(filepath):

        # Check if we can read from the file
        with codecs.open(filepath, 'r', 'utf-8') as fileh:
            try:
                filecont = fileh.read()
            except UnicodeDecodeError:
                logger.error("UnicodeDecodeError on " + filepath + ". Re-downloading it...")
                fileh.close()
                os.unlink(filepath)
                filecont = ''

        # Check if the page served was the one for robots
        if filecont != '':
            if (wasRobotDetected(filecont)):
                logger.warning("Pre-saved file contains robot. Removing it...")
                os.unlink(filepath)
            else:
                logger.debug("Returning content from pre-saved file " + filepath)
                soup = bs.BeautifulSoup(filecont, 'lxml')
                return soup

    # Get actual source code
    logger.debug("Calling getPageSourceCode( " + url + ")")
    cont = getPageSourceCode(url, by_condition, by_value)

    # Get the soup
    # print("type(cont): "+str(type(cont)))
    soup = bs.BeautifulSoup(cont, 'lxml')

    # Save HTML code in file
    with codecs.open(filepath, 'w', 'utf-8') as fileh:
        fileh.write(cont)

    # Check for robot detection
    if wasRobotDetected(cont):
        robot_errors += 1
        sec = random.randint(detected_wait_min, detected_wait_max)
        os.remove(filepath)
        if robot_errors > max_robot_errors:
            logger.critical("Too may robots errors")
            exit()
        else:
            logger.error("ROBOT: I have downloaded a file that contains robot detection: " + filepath + ". Waiting for "+str(sec)+" and then retrying")
            time.sleep(sec)
            return getPageSoup(url, filepath, by_condition, by_value)
    else:
        robot_errors = 0
        logger.debug("File downloaded successfully")
        return soup
