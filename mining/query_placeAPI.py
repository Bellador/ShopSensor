import re
import sys
import time
import psycopg2
import pandas as pd
# uses github repo https://github.com/slimkrazy/python-google-places
sys.path.insert(1, "<ADD HERE PATH TO>/googleplaces")
from googleplaces import GooglePlaces, lang

class PlaceQuerier:
    ''' LOCATION: ZURICH AND ZUG SWITZERLAND
    SEARCH & ACQUIRE GOOGLE PLACE API DATA FOR A LIST OF KEYWORDS FOR LATER POPULAR TIME SCRAPING
    - acquire places and metadata
    - create unique list
    '''

    def __init__(self, search_terms=None, output_file='ZUG_ZURICH_googleplaces.csv', file_sep=';'):
        # lat, lng coordinate pairs, location name and radius used as centroids for radial search queries with the above defined radius
        self.search_locations = [
            #------- Biel
            ([47.099546, 7.234125], 'sutz-lattrigen, Switzerland', 2000),
            ([47.113922, 7.265022], 'port brügg, Switzerland', 2000),
            ([47.128994, 7.300038], 'schwadernau, Switzerland', 2000),
            ([47.156081, 7.302786], 'safern, Switzerland', 2000),
            ([47.145929, 7.261068], 'Biel/Bienne, Switzerland', 2000),
            ([47.132268, 7.225536], 'Biel/Bienne, Switzerland', 2000),
            # ------- Bern
            ([46.942645, 7.396691], 'bümpliz bern, Switzerland', 2000),
            ([46.952256, 7.443040], 'Bern, Switzerland', 2000),
            ([46.967486, 7.485781], 'Ostermundigen bern, Switzerland', 2000),
            ([46.924354, 7.430848], 'spiegel bern, Switzerland', 2000),
            ([46.935144, 7.476516], 'muri bei bern, Switzerland', 2000),
            #----- Ettingen BL
            ([47.481616, 7.544138], 'Ettingen, BL, Switzerland', 3000)
        ]
        # search terms in english and german
        if search_terms is None:
            self.search_terms = [
                            'train stations', 'bus stations', 'tram stations', 'Bahnhof', 'Bushaltestelle', 'Tramstation',
                            'post offices', 'pharmacies', 'bakeries', 'butcheries', 'Post', 'Apotheken', 'Bäckerei',
                            'Metzger', 'Shopping mall', 'Einkaufspasage',
                            'supermarkets', 'convenience stores', 'Lebensmittelladen',
                            'Aldi', 'Aldi Schweiz', 'Coop', 'Migros', 'Denner', 'Lidl', 'Volg', 'Spar', 'Landi',
                            'Kiosk', 'Avec Kiosk', 'Migrolino',
                            'takeaway food', 'takeaway shop', 'pizza shop', 'kebab shop', 'Dönerladen', 'Pizzaria',
                            'gas station', 'petrol station', 'Tankstelle']
        else:
            self.search_terms = search_terms
        # defines the output filename (with all non-unique places!)
        self.raw_output_file = output_file
        self.unique_output_file = output_file[:-4] +'_unique.csv'
        # determines the csv file seperator
        self.file_sep = file_sep
        # header used for the output filename, corresponds to the acquired metadata per place
        self.file_header = f'place_id{self.file_sep}place_name{self.file_sep}address{self.file_sep}zip_code{self.file_sep}lat{self.file_sep}lng{self.file_sep}phone_nr{self.file_sep}open_hours{self.file_sep}rating{self.file_sep}store_url{self.file_sep}google_url{self.file_sep}related_terms{self.file_sep}used_search_term\n'

        # main process
        self.conn = self.conn_db()
        # creates PLACE table if it does not exist already
        self.create_places_table()
        self.df_unique = self.query()
        # populate or update PLACE table with new place metadata
        self.update_places_db()

    def conn_db(self):
        # with open('db_psw.txt', 'rt') as f:
        #     password = f.read()
        # locally
        # conn = psycopg2.connect(host="localhost", port=5432, database="popular_times", user="postgres", password=password)

        # on server
        conn = psycopg2.connect(host="localhost", port=5433, database="<ADD HERE>", user="<ADD HERE>")
        return conn

    def create_places_table(self):
        '''create PLACES table with metadata for the first time'''
        with self.conn.cursor() as cursor:
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS places (
                            place_id TEXT PRIMARY KEY,
                            place_name TEXT,
                            address TEXT,
                            zip_code SMALLINT,
                            lat DOUBLE PRECISION,
                            lng DOUBLE PRECISION,
                            phone_nr TEXT,
                            open_hours TEXT,
                            rating DECIMAL,
                            store_url TEXT,
                            google_url TEXT,
                            related_terms TEXT,
                            used_search_term TEXT,
                            has_google_data BOOLEAN DEFAULT TRUE                  
                            );""")
            ## create indexes
            # cursor.execute("""
            #         CREATE INDEX IF NOT EXISTS index_autotags
            #         ON public.data_100m USING btree
            #         (autotags COLLATE pg_catalog."C" varchar_ops ASC NULLS LAST)
            #         TABLESPACE pg_default;
            #         """)
        self.conn.commit()

    def update_places_db(self):
        '''if PLACES table is emtpy it will be simply populated with the place metadata.
        if it is populated, it will be checked if the google_urls are still up 2 date if not they will be updated
        to ensure that the Popular Times scraper can function properly. Also new place_ids will be added.'''
        with self.conn.cursor() as cursor:
            for index, row in self.df_unique.iterrows():
                cursor.execute("""INSERT INTO places
                (
                place_id,
                place_name,
                address,
                zip_code,
                lat,
                lng,
                phone_nr,
                open_hours,
                rating, 
                store_url,
                google_url,
                related_terms,
                used_search_term
                )            
                VALUES 
                (
                %(place_id)s,
                %(place_name)s,
                %(address)s,
                %(zip_code)s,
                %(lat)s,
                %(lng)s,
                %(phone_nr)s,
                %(open_hours)s,
                %(rating)s,
                %(store_url)s,
                %(google_url)s,
                %(related_terms)s,
                %(used_search_term)s
                )
                ON CONFLICT DO NOTHING;""",
                               {
                               'place_id': row['place_id'],
                               'place_name': row['place_name'],
                               'address': row['address'],
                               'zip_code': row['zip_code'],
                               'lat': row['lat'],
                               'lng': row['lng'],
                               'phone_nr': row['phone_nr'],
                               'open_hours': row['open_hours'],
                               'rating': row['rating'],
                               'store_url': row['store_url'],
                               'google_url': row['google_url'],
                               'related_terms': row['related_terms'],
                               'used_search_term': row['used_search_term']
                               })
        self.conn.commit()
        print('[+] population of table popular_times successful')
        print('[*] checking for google_url updates')
        url_updates = 0
        with self.conn.cursor() as cursor:
            for index, row in self.df_unique.iterrows():
                place_id = row['place_id']
                new_google_url = row['google_url']
                # fetch db row with that place_id (should be fast since place_id is a primary key)
                cursor.execute(f"""SELECT google_url FROM places WHERE place_id = %s""", (place_id,))
                old_google_url = cursor.fetchall()[0][0] # returns a list of tuples for rows. First element of that tuple
                # url update needed
                if new_google_url != old_google_url:
                    url_updates += 1
                    cursor.execute("""UPDATE places SET google_url = %s WHERE place_id = %s""", (new_google_url, place_id))
                    self.conn.commit()
                else:
                    # no update needed
                    pass
        self.conn.commit()
        print(f'[+] updates performed: {url_updates}')

    def load_apikey(self, path='google_cloud_apikey.txt'):
        with open(path, 'rt') as f:
            api_key = f.read()
        return api_key

    def remove_place_dublicates(self):
        '''creates a unique list of Google places since the search terms can return overlapping results'''
        # load csv file as pandas dataframe
        df = pd.read_csv(self.raw_output_file, sep=self.file_sep)
        df_unique = df.drop_duplicates(subset='place_id', inplace=False)
        return df_unique

    '''
    MAIN BLOCK HERE
    '''
    def query(self):
        # write header to output csv file
        with open(self.raw_output_file, 'at', encoding='utf-8') as f:
            f.write(self.file_header)

        google_places = GooglePlaces(self.load_apikey())
        # iterate over different locations containing coordinate pair, location name and radius in meters
        for centroid_nr, search_params in enumerate(self.search_locations, 1):
            lat = search_params[0][0]
            lng = search_params[0][1]
            location_name = search_params[1]
            radius = search_params[2]
            print('\n')
            print('_' * 30)
            print(f'Current: {location_name} - Centroid {centroid_nr} of {len(self.search_locations)}')
            # iterate over search terms:
            for nr_, search_term in enumerate(self.search_terms):
                page = 1
                '''FOR TESTING'''
                # if nr_ == 2:
                #     break

                # You may prefer to use the text_search API, instead.
                while True:
                    try:
                        query_result = google_places.nearby_search(location=location_name,
                                                                   lat_lng={'lat': lat,
                                                                            'lng': lng},
                                                                   radius=radius,
                                                                   keyword=search_term) #, type=place_types.TYPE_CONVENIENCE_STORE
                        break
                    except:
                        time.sleep(60)
                # If types param contains only 1 item the request to Google Places API
                # will be send as type param to fullfil:
                # http://googlegeodevelopers.blogspot.com.au/2016/02/changes-and-quality-improvements-in_16.html
                '''While loop to process remaining pages if present'''
                while True:
                    print(f"\rProcessing search term: {search_term}, page {page}", end='')
                    if query_result.has_attributions:
                        print(query_result.html_attributions)

                    for nr_, place in enumerate(query_result.places):

                        '''FOR TESTING'''
                        # if nr_ == 4:
                        #     break

                        # Returned places from a query are place summaries.
                        try:
                            place_name = place.name.replace(self.file_sep, '')
                        except Exception as e:
                            print(f'\nerror: {e}')
                            place_name = ''
                        try:
                            geo_location = place.geo_location
                            lat = geo_location['lat']
                            lng = geo_location['lng']
                        except Exception as e:
                            print(f'\nerror: {e}')
                            lat, lng = 0.0000
                        try:
                            place_id = place.place_id.replace(self.file_sep, '')
                        except Exception as e:
                            print(f'\nerror: {e}')
                            place_id = ''
                        '''obtain additional metadata per place'''
                        # The following method has to make a further API call.
                        place.get_details()
                        # Referencing any of the attributes below, prior to making a call to
                        # get_details() will raise a googleplaces.GooglePlacesAttributeError.

                        details = place.details # A dict matching the JSON response from Google.
                        try:
                            address = details['formatted_address'].replace(self.file_sep, '')
                        except Exception as e:
                            print(f'\nerror: {e}')
                            address = ''
                        try:
                            # zip codes in switzerland are always four digits long. There should not be a conflict with street numbers since they are smaller
                            zip_pattern = r'([\d]{4})'
                            zip_code = int(re.search(zip_pattern, address).group(1))
                            pass
                        except Exception as e:
                            print(f'\nerror: {e}')
                            zip_code = 0000
                        try:
                            phone_nr = details['international_phone_number'].replace(self.file_sep, '')
                        except Exception as e:
                            phone_nr = ''
                        try:
                            open_hours = ''
                            open_hours_list = details['opening_hours']['weekday_text']
                            for i in open_hours_list:
                                open_hours = open_hours + str(i).replace(self.file_sep, '') + str(',')
                        except Exception as e:
                            open_hours = ''
                        try:
                            store_url = details['website'].replace(self.file_sep, '')
                        except Exception as e:

                            store_url = ''
                        try:
                            rating = float(details['rating'])
                        except Exception as e:
                            rating = ''
                        try:
                            google_url = details['url'].replace(self.file_sep, '')
                        except Exception as e:
                            print(f'error: {e}')
                            google_url = ''
                        try:
                            related_terms = ''
                            related_terms_list = details['types']
                            for i in related_terms_list:
                                related_terms = related_terms + str(i).replace(self.file_sep, '') + str(',')
                        except Exception as e:
                            related_terms = ''

                        # write place to file
                        with open(self.raw_output_file, 'at', encoding='utf-8') as f:
                            line = f'{place_id}{self.file_sep}{place_name}{self.file_sep}{address}{self.file_sep}{zip_code}{self.file_sep}{lat}{self.file_sep}{lng}{self.file_sep}{phone_nr}{self.file_sep}{open_hours}{self.file_sep}{rating}{self.file_sep}{store_url}{self.file_sep}{google_url}{self.file_sep}{related_terms}{self.file_sep}{search_term}\n'
                            f.write(line)

                    '''FOR TESTING'''
                    # break

                    # Are there any additional pages of results?
                    if query_result.has_next_page_token:
                        page += 1
                        while True:
                            try:
                                query_result = google_places.nearby_search(
                                    location=location_name,
                                    lat_lng={'lat': lat,
                                             'lng': lng},
                                    radius=radius,
                                    keyword=search_term,
                                    pagetoken=query_result.next_page_token)
                                break
                            except:
                                time.sleep(60)
                    else:
                        break

        '''after all search terms are prosessed'''
        # load csv file into pandas to remove dublicates
        df_unique = self.remove_place_dublicates()
        # dump to csv
        df_unique.to_csv(self.unique_output_file, sep=self.file_sep, encoding='utf-8')
        return df_unique

PlaceQuerier()