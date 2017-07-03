# cb_scraper
cb_scraper is a web scraper for crunchbase.com.
It uses Selenium as webdriver and BeautifulSoup 4 to process 
the DOM

It can automatically download information about a company or a person

- It downloads company's overview, people list, 
past people list and advisors list
- It also downloads a person's overview and investments
- The downloaded HTML files are scraped using BeautifulSoup 4, 
the result of the processing is saved in a JSON data file

HTML files are also saved, so you can modify the scraping in the future without having to re-download the page

Written using OOP paradigm, adding another endpoint not currently downloaded is incredibly easy