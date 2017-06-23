import codecs
import json
import os
import cbscraper.common

# Scrape organization advisors
def scrapeOrgAdvisors(company_cb_id, html_file_advisors):
    # Get the page
    advisor_url = 'https://www.crunchbase.com/organization/' + company_cb_id + '/advisors'
    print("\tGetting company advisors (" + advisor_url + ")")
    soup_advisors = cbscraper.common.getPageSoup(advisor_url, html_file_advisors)
    if (soup_advisors is False):
        print("\tError while making advisory soup")
        return False

    # Scrape page "advisors" (get both main advisors and additional one with the same code)
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


# Scrape organization people
def scrapeOrgPeople(company_cb_id, html_file_people):
    # Get the page
    people_url = 'https://www.crunchbase.com/organization/' + company_cb_id + '/people'
    print("\tGetting company people (" + people_url + ")")
    soup_people = cbscraper.common.getPageSoup(people_url, html_file_people)
    if (soup_people is False):
        print("\tError in making people soup")
        return False

    # Scrape
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


# Scrape organization people
def scrapeOrgPastPeople(company_cb_id, html_file_people):
    # Get the page
    people_url = 'https://www.crunchbase.com/organization/' + company_cb_id + '/past_people'
    print("\t[scrapeOrgPastPeople]Getting company past_people (" + people_url + ")")
    soup_people = cbscraper.common.getPageSoup(people_url, html_file_people)
    if (soup_people is False):
        print("\tError in making past_people soup")
        return False

    # Scrape
    people = list()
    for div_people in soup_people.find_all('div', class_='past_people'):
        for info_block in div_people.find_all('div', class_='info-block'):
            h4 = info_block.find('h4')
            a = h4.a
            name = a.get('data-name')
            print("[scrapeOrgPastPeople]Found " + name)
            link = a.get('href')

            role = ''
            h5_tag = info_block.find('h5')
            if h5_tag is not None:
                role = h5_tag.text

            name = cbscraper.common.myTextStrip(name)
            role = cbscraper.common.myTextStrip(role)

            people.append([name, link, role])

    return people


# Scrape a company
def scrapeOrganization(org_data):
    # Get variables
    json_file = org_data['json']
    rescrape = org_data['rescrape']
    html_file_overview = org_data['overview_html']
    html_file_people = org_data['people_html']
    html_file_past_people = org_data['past_people_html']
    html_file_advisors = org_data['board_html']
    company_vico_id = org_data['vico_id']
    company_cb_id = org_data['cb_id']

    print("[scrapeOrganization] Scraping company " + company_cb_id)

    # Check if we have a JSON file and if rescrape is False. In this case use the JSON file we already have
    if (os.path.isfile(json_file) and not rescrape):
        print("[scrapeOrganization] Organization already scraped")
        with open(json_file, 'r') as fileh:
            org_data = json.load(fileh)
        return org_data

    # Get the page "overview"
    overview_url = 'https://www.crunchbase.com/organization/' + company_cb_id
    print("\tGetting company overview (" + overview_url + ")")
    soup_overview = cbscraper.common.getPageSoup(overview_url, html_file_overview)
    if (soup_overview is False):
        print("\tError in making overview soup")
        return False

    # Scrape page "overview"

    # Legend: page->section

    # Scrape section overview->overview
    overview = {}

    # Do we have a team?
    has_current_team = False
    tag = soup_overview.find('h2', {'id': 'current_team'})
    if tag is not None:
        has_current_team = True

    # Do we have advisors?
    has_advisors = False
    tag = soup_overview.find('h2', {'id': 'board_members_and_advisors'})
    if tag is not None:
        has_advisors = True

    # Do we have past_people?
    has_past_people = False
    tag = soup_overview.find('h2', {'id': 'past_team'})
    if tag is not None:
        has_past_people = True

    # Headquarters
    tag = soup_overview.find('dt', string='Headquarters:')
    if tag is not None:
        overview['headquarters'] = tag.find_next('dd').text

    # Description
    tag = soup_overview.find('dt', string='Description:')
    if tag is not None:
        overview['description'] = tag.find_next('dd').text

    # Founders
    tag = soup_overview.find('dt', string='Founders:')
    if tag is not None:
        founders_list = tag.find_next('dd').text.split(",")
        overview['founders'] = [x.strip() for x in founders_list]

    # Categories
    tag = soup_overview.find('dt', string='Categories:')
    if tag is not None:
        categories_list = tag.find_next('dd').text.split(",")
        overview['categories'] = [x.strip() for x in categories_list]

    # Website
    tag = soup_overview.find('dt', string='Website:')
    if tag is not None:
        overview['website'] = tag.find_next('dd').text

    # Social
    tag = soup_overview.find('dd', class_="social-links")
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
    company_details_tag = soup_overview.find('div', class_="base info-tab description")

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
    people = []
    if has_current_team:
        print("\tScraping current team...")
        people = scrapeOrgPeople(company_cb_id, html_file_people)

        # Scrape page "advisors"
    advisors = []
    if has_advisors:
        print("\tScraping advisors...")
        advisors = scrapeOrgAdvisors(company_cb_id, html_file_advisors)

        # Scrape page "past people"
    past_people = []
    if has_past_people:
        print("\tScraping past people...")
        past_people = scrapeOrgPastPeople(company_cb_id, html_file_past_people)

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
    with codecs.open(json_file, 'w', 'utf-8') as fileh:
        fileh.write(cbscraper.common.jsonPretty(company_data))

    return company_data
