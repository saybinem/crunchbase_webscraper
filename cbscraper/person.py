import logging
import os
import re

import cbscraper.DateInterval
import cbscraper.PersonScraper
import cbscraper.GenericScraper
from cbscraper.GenericScraper import Error404
import main_cb
import global_vars

def getPersonIdFromLink(link):
    return link.split("/")[2]

# *** Investments ***
def scrapePersonInvestments(inv_soup):
    inv_list = list()
    inv_div = inv_soup.find('div', class_='investments')
    if inv_div is not None:
        for tr in inv_div.table.tbody.find_all('tr'):
            # Date
            td1 = tr.find('td')
            date = td1.text
            # Invested in
            td2 = td1.find_next('td')
            invested_in_link = td2.a.get('href')
            invested_in_text = td2.text
            # Round
            td3 = td2.find_next('td')
            round_text = td3.text
            round_link = td3.a.get('href')
            
            round_arr = round_text.split("/")
            round_amount = round_arr[0].strip()
            round_series = round_arr[1].strip()
            
            # Details
            td4 = td3.find_next('td')
            details_text = td4.text
            details_link = ''
            if (td4.a is not None):
                details_link = td4.a.get('href')
            # append
            inv_list.append(
                [date, invested_in_link, invested_in_text, round_link, round_amount, round_series, details_link, details_text])
            # logging.info("Found investment: "+date + " "+invested_in_text + " " + round_text + " " + details_text)
    return inv_list

# *** Education ***
def scrapePersonEducation(soup):
    education_list = list()
    for edu in soup.find_all('div', class_='education'):
        for info_block in edu.find_all('div', class_='info-block'):

            # School
            institute = ''
            if info_block.h4 is not None:
                institute = info_block.h4.a.text

            # Subject
            subject = ''
            if info_block.h5 is not None:
                subject = info_block.h5.text

            # Date
            date_start, date_end = '', ''
            if info_block.h5 is not None:
                date_int = info_block.h5.next_sibling
                if date_int is not None:
                    date_int_c = cbscraper.DateInterval.DateInterval()
                    date_int_c.fromText(date_int)
                    date_start, date_end = date_int_c.getStart(), date_int_c.getEnd()

            # Put in list
            edu_items = [institute, subject, date_start, date_end]
            education_list.append(edu_items)
    return education_list

# *** Advisory roles ***
def scrapePersonAdvisoryRoles(soup):
    adv_roles = list()
    for advisory_role in soup.find_all('div', class_='advisory_roles'):
        advisory_role_ul = advisory_role.ul
        if advisory_role_ul is not None:
            for li in advisory_role_ul.find_all('li'):
                # logging.debug("Advisory role li: " + li.text)
                info_block = li.div
                role = info_block.h5.text
                company_tag = info_block.h4.a
                company_name = company_tag.text
                company_id = company_tag['data-permalink']
                date = info_block.find('h5', class_='date')
                date_start, date_end = '', ''
                if (date is not None):
                    date_text = date.text
                    if date_text:
                        date_int = cbscraper.DateInterval.DateInterval()
                        date_int.fromText(date_text)
                        date_start, date_end = date_int.getStart(), date_int.getEnd()
                adv_roles.append([role, company_name, date_start, date_end, company_id])
    return adv_roles

# *** Past jobs ***
def scrapePersonPastJobs(soup):
    # Past jobs (experiences -> card-content -> past_job)
    past_jobs = list()
    for div_past_job in soup.find_all('div', class_='past_job'):
        # recursive=False finds only DIRECT children of the div
        for info_row in div_past_job.find_all('div', class_='info-row', recursive=False):
            # skip header and footer
            if info_row.find('div', class_=['header', 'footer'], recursive=False) is not None:
                # print("HEADER OR FOOTER FOUND")
                continue
            date_start_child = info_row.find('div', class_='date')
            date_start = date_start_child.text
            date_end = date_start_child.find_next('div', class_='date').text
            title = info_row.find('div', class_='title').text
            company_cell = info_row.find('div', class_='company')
            company_tag = company_cell.a
            company_name = company_tag.text
            company_id = company_tag['data-permalink']
            past_jobs.append([company_name, title, date_start, date_end, company_id])
            # logging.info("Found past job: "+str(past_job_dict))
    return past_jobs

# *** Current jobs ***
def scrapePersonCurrentJobs(soup):
    # Current jobs  (experiences -> card-content -> current_job)
    current_jobs = list()
    for current_job in soup.find_all('div', class_='current_job'):
        info_block = current_job.find('div', class_='info-block')
        role = info_block.h4.text
        follow_card = info_block.find('a', class_='follow_card')
        company_name = follow_card.text
        company_id = follow_card['data-permalink']
        date = info_block.find('h5', class_='date')
        date_start, date_end = '', ''
        if (date is not None):
            date_text = date.text
            date_int = cbscraper.DateInterval.DateInterval()
            date_int.fromText(date_text)
            date_start, date_end = date_int.getStart(), date_int.getEnd()
        current_jobs.append([role, company_name, date_start, date_end, company_id])
    return current_jobs

# *** Overview ***
def scrapePersonOverview(soup):
    overview = dict()
    overview_content = soup.find(id='info-card-overview-content')

    if overview_content is not None:

        # Primary role
        tag = overview_content.find('dt', string='Primary Role')
        if tag is not None:
            role_arr = tag.find_next('dd').text.split('@')
            overview['primary_role'] = dict()
            overview['primary_role']['role'] = role_arr[0].strip()
            overview['primary_role']['firm'] = role_arr[1].strip()

        # Born date
        tag = overview_content.find('dt', string='Born:')
        if tag is not None:
            overview['born'] = tag.find_next('dd').text

        # Gender
        tag = overview_content.find('dt', string='Gender:')
        if tag is not None:
            overview['gender'] = tag.find_next('dd').text

        # Location
        tag = overview_content.find('dt', string='Location:')
        if tag is not None:
            overview['location'] = tag.find_next('dd').text

        # Social links
        overview['social'] = dict()
        tag = overview_content.find('dt', text=re.compile('Social:.*'))
        if tag:
            social_links = tag.findNext('dd')

            a_tag = social_links.find('a', {'data-icons': 'facebook'})
            if a_tag is not None:
                overview['social']['facebook'] = a_tag.get('href')

            a_tag = social_links.find('a', {'data-icons': 'linkedin'})
            if a_tag is not None:
                overview['social']['linkedin'] = a_tag.get('href')

            a_tag = social_links.find('a', {'data-icons': 'twitter'})
            if a_tag is not None:
                overview['social']['twitter'] = a_tag.get('href')

    return overview

# *** Details ***
def scrapePersonDetails(soup):
    # Get personal details (in the HTML code they are called 'description')
    person_details = ''
    div_description = soup.find('div', {"id": "description"})
    if div_description is not None:
        person_details = div_description.text
        if person_details.find("Click/Touch UPDATE above to add Details for") > 0:
            person_details = ""

    return person_details

# *** Scrape a single person (e.g. "/person/gavin-ray") ***
def scrapePerson(data):

    # Get input vars
    person_id = data['id']
    json_file = data['json']
    type = data['type']
    company_cb_id = data['company_id_cb']
    company_vico_id = data['company_id_vico']

    if (os.path.isfile(json_file) and not global_vars.rescrape):
        logging.info("Person \"" + person_id + "\" already scraped and not re-scraping because global vars say so")
        return True

    logging.debug("Scraping person: '" + person_id + "' of company '"+company_cb_id+"'")

    # Initial build of information
    person_data = {
        'type': type,
        'person_id_cb': person_id,
        'company_id_cb': company_cb_id,
        'company_id_vico': company_vico_id
    }

    # Scrape
    error_code = ''
    person = cbscraper.PersonScraper.PersonScraper(person_id)
    try:
        person.scrape()
    except Error404:
        error_code = '404'
        logging.error("scrape() raised a 404 error")
    else:
        # The try ... except statement has an optional else clause, which, when present, must follow all except clauses.
        # It is useful for code that must be executed if the try clause does not raise an exception
        soup = person.soup_entity
        inv_soup = person.soup_inv

        # Get name
        name = soup.find(id='profile_header_heading').text

        # Scrape
        person_details = scrapePersonDetails(soup)
        overview = scrapePersonOverview(soup)
        current_jobs = scrapePersonCurrentJobs(soup)
        past_jobs = scrapePersonPastJobs(soup)
        adv_roles = scrapePersonAdvisoryRoles(soup)
        education = scrapePersonEducation(soup)
        inv_list = scrapePersonInvestments(inv_soup)

        # Build error code
        if len(current_jobs) == 0:
            error_code += 'NoCurJobs_'
        if len(past_jobs) == 0:
            error_code += 'NoPasJobs_'
        if len(adv_roles) == 0:
            error_code += 'NoAdvRoles_'
        if len(education) == 0:
            error_code += 'NoEdu_'
        if len(inv_list) == 0:
            error_code += 'NoInv_'

        # Add informations
        person_data['name'] = name
        person_data['overview'] = overview
        person_data['person_details'] = person_details
        person_data['current_jobs'] = current_jobs
        person_data['past_jobs'] = past_jobs
        person_data['advisory_roles'] = adv_roles
        person_data['education'] = education
        person_data['investments'] = inv_list

    # Rembemr to save the error code, no matter what has happened
    person_data['error'] = error_code

    # Save to JSON file
    cbscraper.GenericScraper.saveDictToJsonFile(person_data, json_file)

    # Return
    return person_data

# Give a company, scrape current people, past people and advisors
# company_data = a dict returned by cbscraper.company.scrapeOrganization()
# key = the dictionary key that contains the list of lists of company persons
def scrapePersons(company_data, key, company_id_cb = None, company_id_vico = None):
    global rescrape

    if company_id_cb is None:
        company_id_cb = company_data['company_id_cb']

    if company_id_vico is None:
        company_id_vico = company_data['company_id_vico']

    p_list = company_data[key]

    if not p_list:
        logging.debug("List "+key+" is empty for "+company_id_cb)

    for p in p_list:
        person_id = getPersonIdFromLink(p[1])
        person_data = {
            "id": person_id,
            "json": "./data/person/json/" + person_id + ".json",
            'company_id_cb': company_id_cb,
            'company_id_vico': company_id_vico,
            'type': key  # allow to distinguish among "team", "advisors", "past_people" and "founders"
        }
        scrapePerson(person_data)