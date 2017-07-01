import json
import logging
import os

import cbscraper.common
import cbscraper.CompanyScraper

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

            name = cbscraper.common.myTextStrip(name)
            primary_role = cbscraper.common.myTextStrip(primary_role)
            role_in_bod = cbscraper.common.myTextStrip(role_in_bod)

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

            name = cbscraper.common.myTextStrip(name)
            role = cbscraper.common.myTextStrip(role)

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
            name = cbscraper.common.myTextStrip(name)
            role = cbscraper.common.myTextStrip(role)
            people.append([name, link, role])
    return people


# Scrape a company
def scrapeOrganization(org_data):
    # Get variables
    json_file = org_data['json']
    rescrape = org_data['rescrape']
    company_vico_id = org_data['vico_id']
    company_cb_id = org_data['cb_id']

    logging.debug("Scraping company " + company_cb_id)

    # Check if we have a JSON file and if rescrape is False. In this case use the JSON file we already have
    if (os.path.isfile(json_file) and not rescrape):
        logging.warning("Organization already scraped. Returning JSON file")
        with open(json_file, 'r') as fileh:
            org_data = json.load(fileh)
        return org_data

    # Scrape organization
    org = cbscraper.CompanyScraper.CompanyScraper(company_cb_id, './data/company/html')
    org.scrape()
    soup = org.getEntitySoup()

    # Scrape page "overview"

    # Legend: page->section

    # Scrape section overview->overview
    overview = {}

    # Headquarters
    tag = soup.find('dt', string='Headquarters:')
    if tag is not None:
        overview['headquarters'] = tag.find_next('dd').text

    # Description
    tag = soup.find('dt', string='Description:')
    if tag is not None:
        overview['description'] = tag.find_next('dd').text

    # Founders
    tag = soup.find('dt', string='Founders:')
    if tag is not None:
        founders_list = tag.find_next('dd').text.split(",")
        overview['founders'] = [x.strip() for x in founders_list]

    # Categories
    tag = soup.find('dt', string='Categories:')
    if tag is not None:
        categories_list = tag.find_next('dd').text.split(",")
        overview['categories'] = [x.strip() for x in categories_list]

    # Website
    tag = soup.find('dt', string='Website:')
    if tag is not None:
        overview['website'] = tag.find_next('dd').text

    # Social
    tag = soup.find('dd', class_="social-links")
    if tag is not None:

        overview['social'] = {}

        twitter = tag.find('a', class_="twitter")
        if twitter is not None:
            overview['social']['twitter'] = twitter.get('href')

        linkedin = tag.find('a', class_="linkedin")
        if linkedin is not None:
            overview['social']['linkedin'] = linkedin.get('href')

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

    # Scrape page "people"
    people = scrapeOrgCurrentPeople(org.getCurrTeamSoup())

    # Scrape page "advisors"
    advisors = scrapeOrgAdvisors(org.getAdvisorsSoup())

    # Scrape page "past people"
    past_people = scrapeOrgPastPeople(org.getPastTeamSoup())

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
    cbscraper.common.saveDictToJsonFile(company_data, json_file)

    return company_data
