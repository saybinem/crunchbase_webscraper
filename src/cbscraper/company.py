import logging
import os
import sys

import cbscraper.CBCompanyWebScraper
import cbscraper.GenericWebScraper
import cbscraper.person

from cbscraper import global_vars
from cbscraper.CBCompanyData import CBCompanyData, CBCompanyDetails, CBCompanyOverview, CBCompanyOverviewStats
from cbscraper.CBCompanyWebScraper import OrgEndPoint
from cbscraper.CBPersonData import EPersonType
from cbscraper.GenericWebScraper import Error404
from cbscraper.CBCompanyWebScraper import CBCompanyWebScraper
from cbscraper.CBPersonWebScraper import CBPersonWebScraper
import cbscraper.GenericWebScraper as GenericWebScraper
import cbscraper.funcs

# Scraper overview statistics
def scrapeOrgOverviewStats(company_data, soup):

    t_overview_stats = soup.find('div', class_="overview-stats")
    if t_overview_stats is not None:

        # Acquisitions (https://www.crunchbase.com/organization/onxeo#/entity)
        dt_acq = t_overview_stats.find('dt', string='Acquisitions')
        if dt_acq is not None:
            dd_acq = dt_acq.find_next_sibling('dd')
            company_data.overview.stats.acquisitions.num = dd_acq.text # .string returns bs4.NavigableString, .text returns a python str

        # IPO (https://www.crunchbase.com/organization/onxeo#/entity)
        dt_ipo = t_overview_stats.find('dt', string='IPO / Stock')
        if dt_ipo is not None:
            dd_ipo = dt_ipo.find_next_sibling('dd')
            a1 = dd_ipo.a
            a2 = a1.find_next_sibling('a')
            company_data.overview.stats.ipo.fate = a1.text # convert bs4.NavigableString to python str
            company_data.overview.stats.ipo.fate_link = a1.get('href')
            company_data.overview.stats.ipo.date = str(a1.next_sibling) #.next_sibling is a NavigableString. We need to convert it to a Python string
            company_data.overview.stats.ipo.ticker = a2.text # convert bs4.NavigableString to python str

        # Status
        dt_status = t_overview_stats.find('dt', string='Status')
        if dt_status is not None:
            dd_status = dt_status.find_next_sibling('dd')
            company_data.overview.stats.status = dd_status.get_text()

            # DEBUG
            # logging.info("dd_status='"+str(dd_status)+"'")
            # a1 = dd_status.a
            # if a1 is not None:
            #     overview['stats']['status']['fate'] = a1.text
            #     a2 = a1.find_next_sibling('a')
            #     overview['stats']['status']['by'] = a2.text
            #     overview['stats']['status']['date'] = dd_status.find('span', string='on').next_sibling.text
            # else:
            #     overview['stats']['status']['fate'] = dd_status.text

        # Total Equity Funding (TEF)
        dt_total_equity_funding = t_overview_stats.find('dt', string='Total Equity Funding')
        if dt_total_equity_funding is not None:
            # DEBUG
            # logging.info("Found: "+str(dt_total_equity_funding))
            dd_total_equity_funding = dt_total_equity_funding.find_next_sibling('dd')

            founding_amount = dd_total_equity_funding.find('span', class_="funding_amount")
            if founding_amount is not None:
                company_data.overview.stats.tef.funding_amount = founding_amount.text

            founding_rounds = dd_total_equity_funding.find('span', class_="funding_rounds")
            if founding_rounds is not None:
                company_data.overview.stats.tef.funding_rounds = founding_rounds.text
                company_data.overview.stats.tef.funding_investors = dd_total_equity_funding.a.text

        # Most Recent Funding
        dt_most_recent_funding = t_overview_stats.find('dt', string='Most Recent Funding')
        if dt_most_recent_funding is not None:
            dd_most_recent_funding = dt_most_recent_funding.find_next_sibling('dd')

            company_data.overview.stats.mrf = dd_most_recent_funding.get_text()

            # overview['stats']['mrf'] = {}
            # funding_type = dd_most_recent_funding.find('span', class_='funding-type')
            # if funding_type is not None:
            #     overview['stats']['mrf']['funding_type_text'] = funding_type.a.text
            #     overview['stats']['mrf']['funding_type_link'] = funding_type.a.get('href')
            #
            # # The right hand side is a NavigableString
            # overview['stats']['mrf']['date'] = str( dd_most_recent_funding.find('span', class_='connecting').next_sibling )

# Scarpe organization "overview" section
def scrapeOrgOverview(company_data, soup):

    # Company name
    company_data.name = soup.find('h1', id='profile_header_heading').text

    # Headquarters
    tag = soup.find('dt', string='Headquarters:')
    if tag is not None:
        company_data.overview.headquarters = tag.find_next('dd').text

    # Description
    tag = soup.find('dt', string='Description:')
    if tag is not None:
        company_data.overview.description = tag.find_next('dd').text

    # Founders
    tag = soup.find('dt', string='Founders:')
    if tag is not None:
        dd_founders = tag.find_next('dd')
        for link in dd_founders.find_all('a'):
            name = link.attrs['data-name']
            id = link.attrs['data-permalink']
            company_data.founders.append([name, id])

    # Categories
    tag = soup.find('dt', string='Categories:')
    if tag is not None:
        categories_list = tag.find_next('dd').text.split(",")
        company_data.overview.categories = [x.strip() for x in categories_list]

    # Website
    tag = soup.find('dt', string='Website:')
    if tag is not None:
        company_data.overview.website = tag.find_next('dd').text

    # Social links (Facebook, Twitter, LinkedIn)
    tag = soup.find('dd', class_="social-links")
    if tag is not None:
        facebook = tag.find('a', class_="facebook")
        if facebook is not None:
            company_data.overview.social.facebook = facebook.get('href')
        twitter = tag.find('a', class_="twitter")
        if twitter is not None:
            company_data.overview.social.twitter = twitter.get('href')
        linkedin = tag.find('a', class_="linkedin")
        if linkedin is not None:
            company_data.overview.social.linkedin = linkedin.get('href')


# Scrape organization details
def scrapeOrgDetails(company_data, soup):
    # Scrape section "Company Details"
    company_details_tag = soup.find('div', class_="base info-tab description")

    if company_details_tag is not None:

        # Founded year
        tag = company_details_tag.find('dt', string='Founded:')
        if tag is not None:
            company_data.details.founded = tag.find_next('dd').text

        # Closed
        tag = company_details_tag.find('dt', string='Closed:')
        if tag is not None:
            company_data.details.closed = tag.find_next('dd').text

        # Email
        tag = company_details_tag.find('span', class_='email')
        if tag is not None:
            company_data.details.email = tag.text

        # Phone number
        tag = company_details_tag.find('span', class_='phone_number')
        if tag is not None:
            company_data.details.phone_number = tag.text

        # Employees
        tag = company_details_tag.find('dt', string='Employees:')
        if tag is not None:
            emp_str = tag.find_next('dd').text
            emp_arr = emp_str.split("|")
            if len(emp_arr) > 1:
                company_data.details.employees_num = emp_arr[0].strip()
                company_data.details.employees_found = emp_arr[1].strip()
            else:
                company_data.details.employees_num = ''
                company_data.details.employees_found = emp_arr[0].strip()

        # Description
        tag = company_details_tag.find('span', class_='description')
        if tag is not None:
            company_data.details.description = tag.text


# Scrape organization advisors
def scrapeOrgAdvisors(company_data, soup_advisors):
    # Scrape page "advisors" (get both main advisors and additional ones with the same code)
    for div_advisors in soup_advisors.find_all('div', class_='advisors'):
        for info_block in div_advisors.find_all('div', class_='info-block'):
            follow_card = info_block.find('a', class_='follow_card')
            name = follow_card.get('data-name')
            link = follow_card.get('data-permalink')
            primary_role = info_block.h5.text  # the primary role of this person (may not be related to the company at hand)
            role_in_bod = info_block.h6.text  # his role in our company's BoD

            name = cbscraper.funcs.myTextStrip(name)
            primary_role = cbscraper.funcs.myTextStrip(primary_role)
            role_in_bod = cbscraper.funcs.myTextStrip(role_in_bod)

            company_data.advisors.append([name, link, role_in_bod, primary_role])

# Scrape organization current people
def scrapeOrgCurrentPeople(company_data, soup_people):
    for div_people in soup_people.find_all('div', class_='people'):
        for info_block in div_people.find_all('div', class_='info-block'):
            h4 = info_block.find('h4')
            a = h4.a
            name = a.get('data-name')
            link = a.get('href')
            role = info_block.find('h5').text
            name = cbscraper.funcs.myTextStrip(name)
            role = cbscraper.funcs.myTextStrip(role)
            company_data.people.append([name, link, role])

# Scrape organization past people
def scrapeOrgPastPeople(company_data, soup_past_people):
    for div_people in soup_past_people.find_all('div', class_='past_people'):
        for info_block in div_people.find_all('div', class_='info-block'):
            # Get name and link
            h4 = info_block.find('h4')
            a = h4.a
            name = a.get('data-name')
            # logging.info("Found " + name)
            link = a.get('href')
            # Get role
            role = ''
            h5_tag = info_block.find('h5')
            if h5_tag is not None:
                role = h5_tag.text
            # Normalize and append
            name = cbscraper.funcs.myTextStrip(name)
            role = cbscraper.funcs.myTextStrip(role)
            company_data.past_people.append([name, link, role])


# Scrape a company
def scrapeOrg(company_data):

    msg = "Company: {} ({:.2%}) ({})".format(company_data.company_id_cb, company_data.completion_perc,
                                             company_data.company_id_vico)

    # If we have a JSON file, use the JSON file we already have
    out_file = CBCompanyData.genPathFromID(company_data.company_id_cb)

    if os.path.isfile(out_file):
        logging.info(msg + " already scraped. Returning JSON file".format(company_data.company_id_cb))
        org_data = cbscraper.funcs.readJSONFile(out_file)
        return org_data
    else:
        logging.info(msg)

    # Scrape organization
    company_scraper = CBCompanyWebScraper(company_data.company_id_cb)

    # If the HTML file doesn't exist and go_on is False, skip the organization
    htmlfile = company_scraper.genHTMLFilePath(OrgEndPoint.ENTITY)
    if not os.path.isfile(htmlfile):
        if global_vars.new_companies <= 0:
            logging.fatal("File '{}' not found and new_companies='{}' <= 0".format(htmlfile, global_vars.new_companies))
            logging.fatal("NOT WEB-SCRAPING NEW COMPANIES")
            sys.exit(0)
        else:
            global_vars.new_companies -= 1

    # Scrape the company
    error_code = ''
    try:
        company_scraper.scrape()
    except Error404:
        error_code = '404'
        logging.info("Error404 intercepted")
    else:
        # Get soup of various sections
        soup_entity = company_scraper.getEndpointSoup(OrgEndPoint.ENTITY)
        soup_people = company_scraper.getEndpointSoup(OrgEndPoint.PEOPLE)
        soup_adv = company_scraper.getEndpointSoup(OrgEndPoint.ADVISORS)
        soup_past_people = company_scraper.getEndpointSoup(OrgEndPoint.PAST_PEOPLE)

        # Data mining
        scrapeOrgDetails(company_data, soup_entity)
        scrapeOrgOverview(company_data, soup_entity)
        scrapeOrgOverviewStats(company_data, soup_entity)
        scrapeOrgCurrentPeople(company_data, soup_people)
        scrapeOrgAdvisors(company_data, soup_adv)
        scrapeOrgPastPeople(company_data, soup_past_people)

        # Error code
        if len(company_data.people) == 0:
            error_code += 'NoCP_'
        if len(company_data.past_people) == 0:
            error_code += 'NoPP_'
        if len(company_data.advisors) == 0:
            error_code += 'NoA_'
        if len(company_data.founders) == 0:
            error_code += 'NoF_'

    # Save error code
    company_data.error = error_code

    # Write to file
    company_data.save(out_file)

    return company_data


# Scrape an organization and all its people
def scrapeOrgAndPeople(company_data):

    # Scrape the company
    # scrapeOrg can return a new company data structure in case it reads the company from file
    company_data = scrapeOrg(company_data)

    # Scrape persons of the company
    if (company_data is not False and company_data.error != '404'):

        logging.debug("Scraping 'founders'")
        # def scrapePersonsList(company_data, key, company_id_cb = None, company_id_vico = None):
        cbscraper.person.scrapePersonsList(company_data, EPersonType.FOUNDERS)

        logging.debug("Scraping 'people'")
        cbscraper.person.scrapePersonsList(company_data, EPersonType.PEOPLE)

        logging.debug("Scraping 'advisors'")
        cbscraper.person.scrapePersonsList(company_data, EPersonType.ADVISORS)

        logging.debug("Scraping 'past_people'")
        cbscraper.person.scrapePersonsList(company_data, EPersonType.PAST_PEOPLE)

    else:
        logging.debug("scrapeOrganization() returned False. This means there is no company_data")
