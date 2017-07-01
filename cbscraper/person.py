import logging
import os
import re

import cbscraper.DateInterval
import cbscraper.common


def getPersonIdFromLink(link):
    return link.split("/")[2]


# Scrape a single person
# e.g. person_link="/person/gavin-ray"
def scrapePerson(data):
    logger = logging.getLogger("scrapePerson")

    # Get input vars
    person_id = data['id']
    overview_html = data['overview']
    investment_html = data['investment_html']
    json_file = data['json']
    rescrape = data['rescrape']
    type = data['type']

    company_cb_id = data['company_id_cb']
    company_vico_id = data['company_id_vico']

    if (os.path.isfile(json_file) and not rescrape):
        logger.info("Person \"" + person_id + "\" already scraped")
        return True

    logger.info("Scraping person: \"" + person_id + "\"")
    person_link = "/person/" + person_id

    # Get the soup
    soup = cbscraper.common.getPageSoup('https://www.crunchbase.com' + person_link, overview_html, 'id',
                                        'profile_header_heading')
    if (soup is False):
        logger.error("Error during person soup")
        return False

    # Get name
    name = soup.find(id='profile_header_heading').text

    # Get overview information
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

    # Get personal details (in HTML code they are called 'description')
    person_details = ''
    div_description = soup.find('div', {"id": "description"})
    if div_description is not None:
        person_details = div_description.text

    # Current jobs  (experiences -> card-content -> current_job)
    current_jobs = list()
    for current_job in soup.find_all('div', class_='current_job'):
        info_block = current_job.find('div', class_='info-block')
        role = info_block.h4.text
        follow_card = info_block.find('a', class_='follow_card')
        company = follow_card.text
        date = info_block.find('h5', class_='date')
        date_start, date_end = '', ''
        if (date is not None):
            date_text = date.text
            date_int = cbscraper.DateInterval.DateInterval()
            date_int.fromText(date_text)
            date_start, date_end = date_int.getStart(), date_int.getEnd()
        current_jobs.append([role, company, date_start, date_end])

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
            company = info_row.find('div', class_='company').text
            past_jobs.append([company, title, date_start, date_end])
            # logger.info("Found past job: "+str(past_job_dict))

    # Advisory roles
    adv_roles = list()
    for advisory_role in soup.find_all('div', class_='advisory_roles'):
        advisory_role_ul = advisory_role.ul
        if advisory_role_ul is not None:
            logging.debug("Advisory role ul: " + advisory_role_ul.text)
            for li in advisory_role_ul.find_all('li'):
                logging.debug("Advisory role li: " + li.text)
                info_block = li.div
                role = info_block.h5.text
                company = info_block.h4.a.text
                date = info_block.find('h5', class_='date')
                date_start, date_end = '', ''
                if (date is not None):
                    date_text = date.text
                    if date_text:
                        date_int = cbscraper.DateInterval.DateInterval()
                        date_int.fromText(date_text)
                        date_start, date_end = date_int.getStart(), date_int.getEnd()
                adv_roles.append([role, company, date_start, date_end])

    # Education
    education = list()
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
            education.append(edu_items)

    # Investments
    inv_list = list()

    inv_has_more = soup.find('a', attrs={'title' : 'All Investments'}) is not None #look for button "See more investments"
    if(inv_has_more):
        logging.info("Has 'more investments' button")
        inv_soup = cbscraper.common.getPageSoup('https://www.crunchbase.com' + person_link + "/investments", investment_html, 'class_name', 'investments')
    else:
        inv_soup = soup

    inv_div = inv_soup.find('div', class_='investments')
    if inv_div is not None:
        for tr in inv_div.table.tbody.find_all('tr'):
            #Date
            td1 = tr.find('td')
            date = td1.text
            #Invested in
            td2 = td1.find_next('td')
            invested_in_link = td2.a.get('href')
            invested_in_text = td2.text
            #Round
            td3 = td2.find_next('td')
            round_text = td3.text
            round_link = td3.a.get('href')
            #Details
            td4 = td3.find_next('td')
            details_text = td4.text
            details_link = ''
            if(td4.a is not None):
                details_link = td4.a.get('href')
            #append
            inv_list.append([date, invested_in_link, invested_in_text, round_link, round_text, details_link, details_text])
            #logging.info("Found investment: "+date + " "+invested_in_text + " " + round_text + " " + details_text)

    # Build complete data set
    person_data = {
        'name': name,
        'type': type,
        'person_id_cb': person_id,
        'company_id_cb': company_cb_id,
        'company_id_vico': company_vico_id,
        'overview': overview,
        'person_details': person_details,
        'current_jobs': current_jobs,
        'past_jobs': past_jobs,
        'advisory_roles': adv_roles,
        'education': education,
        'investments': inv_list
    }

    # Save to JSON file
    cbscraper.common.saveDictToJsonFile(person_data, json_file)

    # Return
    return person_data
