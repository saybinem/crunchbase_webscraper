import json
import logging
import os

import cbscraper.CompanyScraper
import cbscraper.GenericScraper
from cbscraper.CompanyScraper import OrgEndPoint
import cbscraper.person

import main_cb

# Scrape organization advisors
def scrapeOrgAdvisors(soup_advisors):
    # Scrape page "advisors" (get both main advisors and additional ones with the same code)
    advisors = list()
    for div_advisors in soup_advisors.find_all('div', class_='advisors'):
        for info_block in div_advisors.find_all('div', class_='info-block'):
            follow_card = info_block.find('a', class_='follow_card')
            name = follow_card.get('data-name')
            link = follow_card.get('data-permalink')
            primary_role = info_block.h5.text  # the primary role of this person (may not be related to the company at hand)
            role_in_bod = info_block.h6.text  # his role in our company's BoD

            name = cbscraper.GenericScraper.myTextStrip(name)
            primary_role = cbscraper.GenericScraper.myTextStrip(primary_role)
            role_in_bod = cbscraper.GenericScraper.myTextStrip(role_in_bod)

            advisors.append([name, link, role_in_bod, primary_role])

    return advisors


# Scrape organization current people
def scrapeOrgCurrentPeople(soup_people):
    people = list()
    for div_people in soup_people.find_all('div', class_='people'):
        for info_block in div_people.find_all('div', class_='info-block'):
            h4 = info_block.find('h4')
            a = h4.a
            name = a.get('data-name')
            link = a.get('href')
            role = info_block.find('h5').text

            name = cbscraper.GenericScraper.myTextStrip(name)
            role = cbscraper.GenericScraper.myTextStrip(role)

            people.append([name, link, role])

    return people


# Scrape organization past people
def scrapeOrgPastPeople(soup_past_people):
    people = list()
    for div_people in soup_past_people.find_all('div', class_='past_people'):
        for info_block in div_people.find_all('div', class_='info-block'):
            #Get name and link
            h4 = info_block.find('h4')
            a = h4.a
            name = a.get('data-name')
            #logging.info("Found " + name)
            link = a.get('href')
            #Get role
            role = ''
            h5_tag = info_block.find('h5')
            if h5_tag is not None:
                role = h5_tag.text
            #Normalize and append
            name = cbscraper.GenericScraper.myTextStrip(name)
            role = cbscraper.GenericScraper.myTextStrip(role)
            people.append([name, link, role])
    return people

#Scrape organization details
def scrapeOrgDetails(soup):
    # Scrape section overview->company details
    company_details = {}
    company_details_tag = soup.find('div', class_="base info-tab description")

    if company_details_tag is not None:

        # Founded year
        tag = company_details_tag.find('dt', string='Founded:')
        if tag is not None:
            company_details['founded'] = tag.find_next('dd').text

        # Email
        tag = company_details_tag.find('span', class_='email')
        if tag is not None:
            company_details['email'] = tag.text

        # Phone number
        tag = company_details_tag.find('span', class_='phone_number')
        if tag is not None:
            company_details['phone_number'] = tag.text

        # Employees
        tag = company_details_tag.find('dt', string='Employees:')
        if tag is not None:
            emp_str = tag.find_next('dd').text
            emp_arr = emp_str.split("|")
            company_details['employees_num'] = emp_arr[0].strip()
            if len(emp_arr) > 1:
                company_details['employees_found'] = emp_arr[1].strip()

        # Phone number
        tag = company_details_tag.find('span', class_='description')
        if tag is not None:
            company_details['description'] = tag.text

    return company_details

def scrapeOrgOverview(soup):
    # Scrape section overview->overview
    overview = {}

    # Headquarters
    overview['headquarters'] = ''
    tag = soup.find('dt', string='Headquarters:')
    if tag is not None:
        overview['headquarters'] = tag.find_next('dd').text

    # Description
    overview['description'] = ''
    tag = soup.find('dt', string='Description:')
    if tag is not None:
        overview['description'] = tag.find_next('dd').text

    # Founders
    overview['founders'] = ''
    tag = soup.find('dt', string='Founders:')
    if tag is not None:
        founders_list = tag.find_next('dd').text.split(",")
        overview['founders'] = [x.strip() for x in founders_list]

    # Categories
    overview['categories'] = list()
    tag = soup.find('dt', string='Categories:')
    if tag is not None:
        categories_list = tag.find_next('dd').text.split(",")
        overview['categories'] = [x.strip() for x in categories_list]

    # Website
    overview['website'] = ''
    tag = soup.find('dt', string='Website:')
    if tag is not None:
        overview['website'] = tag.find_next('dd').text

    # Social
    overview['social'] = {
        'twitter' : '',
        'linkedin' : ''
    }
    tag = soup.find('dd', class_="social-links")
    if tag is not None:
        twitter = tag.find('a', class_="twitter")
        if twitter is not None:
            overview['social']['twitter'] = twitter.get('href')
        linkedin = tag.find('a', class_="linkedin")
        if linkedin is not None:
            overview['social']['linkedin'] = linkedin.get('href')

    # Statistics
    overview['stats'] = {}
    overview['stats']['acquisitions'] = {}
    overview['stats']['ipo'] = {
        'fate':'',
        'fate_link':'',
        'date':'',
        'ticker':''
    }
    overview['stats']['status'] = ''
    overview['stats']['tef'] = {
        'funding_amount' : '',
        'funding_rounds' : '',
        'funding_investors' : ''
    }
    overview['stats']['mrf'] = ''

    t_overview_stats = soup.find('div', class_="overview-stats")
    if t_overview_stats is not None:

        #Acquisitions (https://www.crunchbase.com/organization/onxeo#/entity)
        dt_acq = soup.find('dt', string='Acquisitions')
        if dt_acq is not None:
            dd_acq = dt_acq.find_next_sibling('dd')
            overview['stats']['acquisitions']['num'] = dd_acq.string

        #IPO (https://www.crunchbase.com/organization/onxeo#/entity)
        dt_ipo = soup.find('dt', string='IPO / Stock')
        if dt_ipo is not None:
            dd_ipo = dt_ipo.find_next_sibling('dd')
            a1 = dd_ipo.a
            overview['stats']['ipo']['fate'] = a1.string
            overview['stats']['ipo']['fate_link'] = a1.get('href')
            overview['stats']['ipo']['date'] = str(a1.next_sibling)
            a2 = a1.find_next_sibling('a')
            overview['stats']['ipo']['ticker'] = a2.string

        # Status
        dt_status = soup.find('dt', string='Status')
        if dt_status is not None:
            dd_status = dt_status.find_next_sibling('dd')
            overview['stats']['status'] = dd_status.string

            # DEBUG
            # logging.info("dd_status='"+str(dd_status)+"'")
            # a1 = dd_status.a

            # if a1 is not None:
            #     overview['stats']['status']['fate'] = a1.string
            #     a2 = a1.find_next_sibling('a')
            #     overview['stats']['status']['by'] = a2.string
            #     overview['stats']['status']['date'] = dd_status.find('span', string='on').next_sibling.string
            # else:
            #     overview['stats']['status']['fate'] = dd_status.string

        # Total Equity Funding (TEF)
        dt_total_equity_funding = soup.find('dt',string='Total Equity Funding')
        if dt_total_equity_funding is not None:
            #DEBUG
            #logging.info("Found: "+str(dt_total_equity_funding))
            dd_total_equity_funding = dt_total_equity_funding.find_next_sibling('dd')

            founding_amount = dd_total_equity_funding.find('span', class_="funding_amount")
            if founding_amount is not None:
                overview['stats']['tef']['funding_amount'] = founding_amount.text

            founding_rounds = dd_total_equity_funding.find('span', class_="funding_rounds")
            if founding_rounds is not None:
                overview['stats']['tef']['funding_rounds'] = founding_rounds.text

            overview['stats']['tef']['funding_investors'] = dd_total_equity_funding.a.text

        # Most Recent Funding
        dt_most_recent_funding = soup.find('dt', string='Most Recent Funding')
        if dt_most_recent_funding is not None:

            dd_most_recent_funding = dt_most_recent_funding.find_next_sibling('dd')

            overview['stats']['mrf'] = dd_most_recent_funding.string

            # overview['stats']['mrf'] = {}
            # funding_type = dd_most_recent_funding.find('span', class_='funding-type')
            # if funding_type is not None:
            #     overview['stats']['mrf']['funding_type_text'] = funding_type.a.text
            #     overview['stats']['mrf']['funding_type_link'] = funding_type.a.get('href')
            #
            # # The right hand side is a NavigableString
            # overview['stats']['mrf']['date'] = str( dd_most_recent_funding.find('span', class_='connecting').next_sibling )

    return overview

# Scrape a company
def scrapeOrganization(org_data):

    # Get variables
    json_file = org_data['json']
    rescrape = org_data['rescrape']
    go_on = org_data['go_on']
    company_vico_id = org_data['vico_id']
    company_cb_id = org_data['cb_id']
    completion_perc = org_data['completion_perc']

    msg = "Company: " + company_cb_id + " (" + str(completion_perc) + "%)"
    logging.warning(msg)

    # Check if we have a JSON file and if rescrape is False. In this case use the JSON file we already have
    if os.path.isfile(json_file) :
        if not rescrape:
            logging.warning("Organization already scraped. Returning JSON file")
            with open(json_file, 'r') as fileh:
                org_data = json.load(fileh)
            return org_data
        else:
            os.unlink(json_file)

    # Scrape organization
    org = cbscraper.CompanyScraper.CompanyScraper(company_cb_id)
    htmlfile = org.genHTMLFilePath(OrgEndPoint.ENTITY)

    # Check if HTML file already exist
    if not os.path.isfile(htmlfile) and not go_on:
        #HTML file does not exists and we are not scraping new companies
        if not go_on:
            logging.info("NOT WEB-SCRAPING NEW COMPANIES")
            return False

    #Scrape the company
    if not org.scrape():
        logging.info("scrape() returned false. Returning false")
        return False

    # Get soup of various sections
    soup_entity = org.getEndpointSoup(OrgEndPoint.ENTITY)
    soup_people = org.getEndpointSoup(OrgEndPoint.PEOPLE)
    soup_adv = org.getEndpointSoup(OrgEndPoint.ADVISORS)
    soup_past_people = org.getEndpointSoup(OrgEndPoint.PAST_PEOPLE)

    # Data scraping
    company_details = scrapeOrgDetails(soup_entity)
    overview = scrapeOrgOverview(soup_entity)
    people = scrapeOrgCurrentPeople(soup_people)
    advisors = scrapeOrgAdvisors(soup_adv)
    past_people = scrapeOrgPastPeople(soup_past_people)

    # Return data
    company_data = {
        'company_id_vico': company_vico_id,
        'company_id_cb': company_cb_id,
        'overview': overview,
        'company_details': company_details,
        'people': people,
        'advisors': advisors,
        'past_people': past_people
    }

    # Write to file
    cbscraper.GenericScraper.saveDictToJsonFile(company_data, json_file)

    return company_data

# Give a company, scrape current people, past people and advisors
# company_data = a dict returned by cbscraper.company.scrapeOrganization()
# key = the dictionary key that contains the list of lists of company persons

def scrapePersons(company_data, key):
    rescrape = main_cb.rescrape

    company_cb_id = company_data['company_id_cb']
    company_vico_id = company_data['company_id_vico']
    p_list = company_data[key]

    if not p_list:
        logging.debug("List "+key+" is empty for "+company_cb_id)

    for p in p_list:
        person_id = cbscraper.person.getPersonIdFromLink(p[1])
        person_data = {
            "id": person_id,
            "json": "./data/person/json/" + person_id + ".json",
            "rescrape": rescrape,
            'company_id_cb': company_cb_id,
            'company_id_vico': company_vico_id,
            'type': key  # allow to distinguish among "team", "advisors" and "past_people"
        }
        cbscraper.person.scrapePerson(person_data)

def scrapeOrgAndPeople(org_data):

    company_data = scrapeOrganization(org_data)

    # Scrape persons of the company

    if (company_data is not False):

        logging.debug("Scraping persons")
        scrapePersons(company_data, 'people')

        logging.debug("Scraping advisors")
        scrapePersons(company_data, 'advisors')

        logging.debug("Scraping past_people")
        scrapePersons(company_data, 'past_people')

    else:
        logging.error("scrapeOrganization() returned False. This means there is no company_data")
