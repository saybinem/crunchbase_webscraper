import logging
import os
import re

import cbscraper.DateInterval
import cbscraper.CBPersonWebScraper
from cbscraper import GenericWebScraper
from cbscraper.GenericWebScraper import Error404
from cbscraper import global_vars
from cbscraper.CBPersonData import CBPersonData, CBPersonDataOverview

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
            invested_in_link = td2.a.get('href') #link
            invested_in_text = td2.text #name of the company

            # Round
            td3 = td2.find_next('td')

            round_link = td3.a.get('href') #link to round CB page
            
            round_arr = td3.text.split("/")
            round_amount = round_arr[0].strip() #amount invested
            round_series = round_arr[1].strip() #series
            
            # Details
            td4 = td3.find_next('td')
            details_text = td4.text
            details_link = ''
            if (td4.a is not None):
                details_link = td4.a.get('href')

            # append to output list
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
                company_id = company_tag['tagged_data-permalink']
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
            company_id = company_tag['tagged_data-permalink']
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
        company_id = follow_card['tagged_data-permalink']
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
    overview = CBPersonDataOverview()

    overview_content = soup.find(id='info-card-overview-content')

    if overview_content is not None:

        # Primary role
        tag = overview_content.find('dt', string='Primary Role')
        if tag is not None:
            role_arr = tag.find_next('dd').text.split('@')
            overview.primary_role.role = role_arr[0].strip()
            overview.primary_role.firm = role_arr[1].strip()

        # Date of birth
        tag = overview_content.find('dt', string='Born:')
        if tag is not None:
            overview.born = tag.find_next('dd').text

        # Gender
        tag = overview_content.find('dt', string='Gender:')
        if tag is not None:
            overview.gender = tag.find_next('dd').text

        # Location
        tag = overview_content.find('dt', string='Location:')
        if tag is not None:
            overview.location = tag.find_next('dd').text

        # Social links
        tag = overview_content.find('dt', text=re.compile('Social:.*'))
        if tag:
            social_links = tag.findNext('dd')

            # Facebook
            a_tag = social_links.find('a', {'tagged_data-icons': 'facebook'})
            if a_tag is not None:
                overview.social.facebook = a_tag.get('href')

            # LinkedIn
            a_tag = social_links.find('a', {'tagged_data-icons': 'linkedin'})
            if a_tag is not None:
                overview.social.linkedin = a_tag.get('href')

            # Twitter
            a_tag = social_links.find('a', {'tagged_data-icons': 'twitter'})
            if a_tag is not None:
                overview.social.twitter = a_tag.get('href')

    return overview

# *** Details ***
def scrapePersonDetails(soup):
    # Get personal details (in the HTML code they are called 'description')
    person_details = ''
    div_description = soup.find('div', {"id": "description"})
    if div_description is not None:
        person_details = div_description.text
        if "Click/Touch UPDATE above to add Details" in person_details:
            person_details = ""
    return person_details

# Name of the person
def scrapePersonName(soup):
    return soup.find(id="profile_header_heading").text

# *** Scrape a single person (e.g. "/person/gavin-ray") ***
def scrapePerson(person_data):

    person_out_file = CBPersonData.genPathFromId(person_data.person_id_cb)

    if (os.path.isfile(person_out_file)):
        logging.debug("Person \"" + person_data.person_id_cb + "\" already scraped")
        return True

    logging.info("Scraping person: '" + person_data.person_id_cb + "' of company '" + person_data.company_id_cb + "'")

    # Scrape
    person_scraper = cbscraper.CBPersonWebScraper.CBPersonWebScraper(person_data.person_id_cb)
    try:
        person_scraper.scrape()
    except Error404:
        person_data.error = '404'
        logging.error("scrape() raised a 404 error")
    else:
        # The try ... except statement has an optional else clause, which, when present, must follow all except clauses.
        # It is useful for code that must be executed if the try clause does not raise an exception
        soup = person_scraper.soup_entity
        inv_soup = person_scraper.soup_inv

        # Scrape
        person_data.name = scrapePersonName(soup)
        person_data.person_details = scrapePersonDetails(soup)
        person_data.overview = scrapePersonOverview(soup)
        person_data.current_jobs = scrapePersonCurrentJobs(soup)
        person_data.past_jobs = scrapePersonPastJobs(soup)
        person_data.advisory_roles = scrapePersonAdvisoryRoles(soup)
        person_data.education = scrapePersonEducation(soup)
        person_data.investments = scrapePersonInvestments(inv_soup)

        # Build error code
        if len(person_data.current_jobs) == 0:
            person_data.stat_code += 'NoCurJobs_'
        if len(person_data.past_jobs) == 0:
            person_data.stat_code += 'NoPasJobs_'
        if len(person_data.advisory_roles) == 0:
            person_data.stat_code += 'NoAdvRoles_'
        if len(person_data.education) == 0:
            person_data.stat_code += 'NoEdu_'
        if len(person_data.investments) == 0:
            person_data.stat_code += 'NoInv_'

    # Save to JSON file
    person_data.save(person_out_file)

    # Return
    return person_data

# Give a company, scrape current people, past people and advisors
# company_data = a dict returned by cbscraper.company.scrapeOrganization()
# key = the dictionary key that contains the list of lists of company persons
def scrapePersonsList(company_data, key):

    company_id_cb = company_data.company_id_cb
    company_id_vico = company_data.company_id_vico

    p_list = getattr(company_data, key)

    if not p_list:
        logging.debug("List "+key+" is empty for "+company_id_cb)

    for p in p_list:
        person_id = getPersonIdFromLink(p[1])

        if person_id in global_vars.already_scraped:
            logging.debug("The person '" + person_id + "' has already been scraped in this session. Just adding new type")
            person_data_file = CBPersonData.genPathFromId(person_id)
            person_data = cbscraper.GenericWebScraper.readJSONFile(person_data_file)
            person_data.setType(key)
            person_data.save(person_data_file, overwrite=True)
        else:
            person_data = CBPersonData()
            person_data.person_id_cb = person_id
            person_data.company_id_cb = company_id_cb
            person_data.company_id_vico = company_id_vico
            person_data.setType(key)
            scrapePerson(person_data)
            global_vars.already_scraped.append(person_data.person_id_cb)