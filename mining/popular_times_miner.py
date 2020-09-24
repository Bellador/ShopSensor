import re
import sys
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

'''
Step 1. Set up a database (CSV shoul be enough, not huge data) containing all supermarkets in Zurich and their location (ZIP code) and respective google maps page
Step 2. Mine those
Step 3. Show a map with the current relative customer load (maybe absolute if shops release historical customer statistics) 

IMPORTANT NOTICE TOGETHER WITH THE USAGE OF WebDriverWait - it has different stages it can wait for:
- presence_of_element_located: (fastest) returns the WebElement once it is located
- visibility_of_element_located: (medium wait) returns the WebElement once it is located and visible
(!!!USE FOLLOWING ONE IF ATTRIBUTES MUST BE ACCESSED OR INTERACTED)
- element_to_be_clickable: (longest wait) returns the WebElement once it is visible, enabled and interactable (i.e. clickable).
'''

class SupermarketMeter:

    def __init__(self, market_list='markets{date}.csv'):
        self.delay = 3  # seconds
        self.error_limit = 3
        self.csv_sep = ';'
        # self.market_list_output = market_list.format(date=datetime.today().strftime('%Y%m%d'))
        # self.input_dict = self.get_input_params()
        self.driver = self.init_webdriver()
        # self.search_supermarkets()

    def get_input_params(self, path='input.txt'):
        with open(path) as f:
            content = f.read()
        input_dict = json.loads(content)
        return input_dict

    def init_webdriver(self):
        # run Firefox in headless mode to increase performance
        self.options = Options()
        self.options.headless = True
        # for running on the local windows machine
        # self.binary = FirefoxBinary(r'C:\Program Files\Mozilla Firefox\firefox.exe')
        # when running on the remote cluster
        self.binary = FirefoxBinary(r'/usr/bin/firefox')
        #initiate the Selenium driver
        driver = webdriver.Firefox(options=self.options, firefox_binary=self.binary)
        return driver

    def get_populartimes(self, place_url):
        self.driver.get(place_url)
        '''
        check for a google agreement form and press 'remind later' (since it obscures the 'next' button of the search results
        '''
        google_agreement_xpath = "//div[@class='widget-consent-dialog']//button[@class='widget-consent-button-later ripple-container']"
        errors_ = 0
        while True:
            try:
                agree_button = WebDriverWait(self.driver, self.delay).until(EC.element_to_be_clickable((By.XPATH, google_agreement_xpath)))
                agree_button.click()
                break
            except Exception as e:
                errors_ += 1
                if errors_ >= self.error_limit:
                    break
        '''
        first check if the popular times GRAPH can be found on the page -> means there is potentially google popular times data 
        but NOT necessarily current busyness numbers!
        '''
        has_google_data = False
        popular_times_graph_xpath = "//div[contains(@class, 'popular-times-graph')]"
        errors_ = 0
        while True:
            try:
                popular_times_graph = WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, popular_times_graph_xpath)))
                has_google_data = True
                break
            except Exception as e:
                errors_ += 1
                if errors_ >= self.error_limit:
                    has_google_data = False
                    break
                # print(f'popular times error: {e}, url: {place_url}')
            # when target item is still obscured - means not fully loaded or at the end of the search results
            except ElementClickInterceptedException:
                errors_ += 1
                print('\r[*] loading...', end='')
                if errors_ >= self.error_limit:
                    break
        '''
        only continue if POTENTIAL google data has been found otherwise skip
        '''
        if has_google_data:
            '''
            find the general description of the current customer load e.g. 'nicht stark besucht'
            '''
            txt_desc_curr_load_xpath = "//div[@class='section-popular-times-busyness-description-container section-popular-times-busyness-description-container-visible']//div[@class='section-popular-times-live-description']"
            errors_ = 0
            while True:
                try:
                    curr_load_desc = WebDriverWait(self.driver, self.delay).until(EC.element_to_be_clickable((By.XPATH, txt_desc_curr_load_xpath)))
                    text_desc_curr_load = str(curr_load_desc.text)
                    break
                except Exception as e:
                    errors_ += 1
                    if errors_ >= self.error_limit:
                        break
                    # print(f'popular times error: {e}, url: {place_url}')
                # when target item is still obscured - means not fully loaded or at the end of the search results
                except ElementClickInterceptedException:
                    errors_ += 1
                    print('\r[*] loading...', end='')
                    if errors_ >= self.error_limit:
                        break
            errors_ = 0
            error_occurred = False
            if errors_ < self.error_limit:
                '''
                find the current and usual customer load at the given time 
                '''
                key_words = ['Derzeit', 'Currently']
                curr_usual_load_xpath = """//div[contains(@class, 'section-popular-times-bar') and contains(@aria-label, '{}') or contains(@aria-label, '{}')]""".format(key_words[0], key_words[1]) #//div[@class='section-popular-times-graph section-popular-times-graph-visible']
                # find the correct div by search for these keywords (german, english) that indicate the div that provides the current load compared to usual
                while True:
                    if errors_ < self.error_limit:
                        try:
                            curr_usual_load = WebDriverWait(self.driver, self.delay).until(EC.element_to_be_clickable((By.XPATH, curr_usual_load_xpath)))
                            text_curr_usual_load = curr_usual_load.get_attribute('aria-label')
                            if error_occurred:
                                print(f'[+] still managed to fetch data...')
                            break
                        except Exception as e:
                            error_occurred = True
                            errors_ += 1
                            if errors_ >= self.error_limit:
                                break
                            # print(f'[-] curr usual load error: {e}')
                        # when target item is still obscured - means not fully loaded or at the end of the search results
                        except ElementClickInterceptedException:
                            errors_ += 1
                            print('\r[*] loading...', end='')
                            if errors_ >= self.error_limit:
                                break
                    else:
                        break
                '''
                use regex to find the values in the optained text string
                two numbers, the first describing the current state and the other the usual
                '''
                try:
                    pattern = r'([\d]{1,3})'
                    matches = re.findall(pattern, text_curr_usual_load)
                    current_popularity = int(matches[0])
                    usual_popularity = int(matches[1])
                    print('_' * 30)
                    print(f'[+] Popularity for url: {place_url}')
                    print(f'[+] {text_desc_curr_load}')
                    print(f'[+] currently: {current_popularity}%, usually: {usual_popularity}%')
                    print(f'[*] fetched at: {datetime.now()}')
                    print('_' * 30)
                    return  has_google_data, text_desc_curr_load, current_popularity, usual_popularity
                except:
                    # print(f'[-] no popularity data found for url: {place_url}')
                    return has_google_data, None, None, None
        else:
            return has_google_data, None, None, None


    def search_supermarkets(self):
        search_terms = self.input_dict['search_terms']
        for term in search_terms:
            print(f"[+] scraping with search term '{term}'")
            self.driver.get(self.input_dict['link'])
            inputElement = self.driver.find_element_by_id("searchboxinput")
            # inputElement.send_keys('Aldi Schweiz Zurich')
            inputElement.send_keys(term)
            #simulate hitting ENTER
            inputElement.send_keys(Keys.ENTER)
            # or if it is a form submit
            #inputElement.submit()
            # time.sleep(self.delay)
            # print("finished sleeping")
            '''
            check for a google agreement form and press 'remind later' (since it obscures the 'next' button of the search results
            '''
            time.sleep(self.delay)
            try:
                agree_button = self.driver.find_element_by_xpath("//div[@class='widget-consent-dialog']//button[@class='widget-consent-button-later ripple-container']")
                agree_button.click()
            except:
                pass
            '''
            ITERATE SEARCH FIELDS
            go to the next search result page by simulating button press
            '''
            page = 1
            print(f"[+] fetching current market list")
            while True:
                try:
                    self.get_markets(term, page)
                    next_button = WebDriverWait(self.driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'n7lv7yjyC35__section-pagination-button-next')))
                    next_button.click()
                    page += 1
                # when target item is still obscured - means not fully loaded or at the end of the search results
                except ElementClickInterceptedException:
                    print('\r[*] loading...', end='')

    def get_markets(self, term: str, page: int):
        results_per_page = 20 #thats what I experienced so far. Helps to identify the correct market results by id
        # xpath to the different place search results inside the scroll bar
        markets_xpath = "//div[@class='section-layout section-layout-root']//div[@class='section-result' and @data-result-index='{insert_}']"
        for index in range(1, results_per_page):
            print(f'\r[*] search term: {term}, page {page}, item {index}', end='')
            while True:
                try:
                    market_result = WebDriverWait(self.driver, self.delay).until(EC.element_to_be_clickable((By.XPATH, markets_xpath.format(insert_=index))))
                    # click on market result to obtain url for later direct accessing
                    time.sleep(self.delay)
                    market_result.click()
                    # get place URL
                    time.sleep(self.delay)
                    market_url = self.driver.current_url
                    break
                except Exception as e:
                    print(f'[-] market result error: {e}')
                # when target item is still obscured - means not fully loaded or at the end of the search results
                except ElementClickInterceptedException:
                    print('\r[*] loading...', end='')
            lat, lng = self.extract_coordinates(market_url)
            # get location data to that Google Place
            location_dict = self.get_location()
            self.write_to_output(market_url, location_dict, lat, lng, term)
            # click on the return button to get back to the other search results
            return_button_xpath = "//div[@class='section-layout section-layout-root']//button[@class='section-back-to-list-button blue-link noprint']"
            while True:
                try:
                    return_button = WebDriverWait(self.driver, self.delay).until(EC.element_to_be_clickable((By.XPATH, return_button_xpath)))
                    # go back to the original result page
                    return_button.click()
                    break
                except Exception as e:
                    print(f'[-] return button error: {e}')

    def extract_coordinates(self, url: str):
        try:
            pattern = r'/@([\d.]+,[\d.]+),(?=\d+z/data)'
            coordinates = re.search(pattern, url).group(1)
            lat, lng = coordinates.split(',')
        except Exception as e:
            print(f'[-] coordinate error: {e}')
        return lat, lng

    def get_location(self):
        '''
        location provided by a Google Place name can be as follows: Förrlibuckstrasse 62, 8005 Zürich
        Therefore left of the comma is the road, right is the ZIP code and the City name
        :return:
        '''
        location_xpath = "//div[@class='section-info-line']//span[@class='widget-pane-link' and @role='text']"
        location_dict = {
            'street': None,
            'city': None,
            'zip': None
                    }
        while True:
            try:
                location = WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, location_xpath)))
                location_txt  = str(location.text)
                location_dict['street'] = location_txt.split(',')[-2]
                location_dict['city'] = location_txt.split(',')[-1].strip().split(' ')[1]
                location_dict['zip'] = location_txt.split(',')[-1].strip().split(' ')[0]
                break
            except Exception as e:
                print('\r[*] loading...', end='')
                # print(f'location error: {e}')
        return location_dict

    def write_to_output(self, url: str, location_dict: dict, lat: str, lng: str, search_term: str):
        with open(self.market_list_output, 'at', encoding='utf-8') as f:
            f.write(f"{url}{self.csv_sep}{location_dict['street']}{self.csv_sep}{location_dict['city']}{self.csv_sep}{location_dict['zip']}{self.csv_sep}{lat}{self.csv_sep}{lng}{self.csv_sep}{search_term}\n")

if __name__ == '__main__':
    init = SupermarketMeter()
    # example
    init.get_populartimes('https://maps.google.com/?cid=12733162641057635049')