import os
import sys
import time
import pandas as pd
from datetime import datetime
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base, as_declarative, declared_attr
from sqlalchemy import create_engine, Column, Integer, DateTime, String, Boolean, update
from mining.popular_times_miner import SupermarketMeter

class PlacesQuerier:
    # Configure Database
    if "DATABASE_URL" in os.environ:
        engine = create_engine(os.environ["DATABASE_URL"], max_overflow=-1)
    else:
        with open("../database.txt") as f:
            # IMPORTANT: NULLPOOL ENSURES THAT NO CONNECTIONS ARE SHARED AMONG CHILDPROCESSES. EVERYONE GETS A NEW CONNECTION!!!!!
            engine = create_engine(f.readline(), poolclass=NullPool) #, poolclass=NullPool #max_overflow=-1,

    # base for the SqlAlchemy classes
    Base = declarative_base()
    Base.metadata.create_all(engine)

    class Entry(Base):
        __tablename__ = 'entries'
        __table_args__ = {'extend_existing': True}
        id = Column(Integer, primary_key=True)
        place_id = Column(String)  # not primary key since there will be multiple entries per place id!
        normal_popularity = Column(Integer)
        current_popularity = Column(Integer)
        current_popularity_desc = Column(String)
        at_time_str = Column(DateTime, default=datetime.now)
        at_time_unix = Column(Integer)

        def __init__(self, place_id, normal_popularity, current_popularity, current_popularity_desc, at_time_str,
                     at_time_unix):
            self.place_id = place_id
            self.normal_popularity = normal_popularity
            self.current_popularity = current_popularity
            self.current_popularity_desc = current_popularity_desc
            self.at_time_str = at_time_str
            self.at_time_unix = at_time_unix

    class Places(Base):
        __tablename__ = 'places'
        __table_args__ = {'extend_existing': True}
        place_id = Column(String, primary_key=True)
        has_google_data = Column(Boolean)

        def __init__(self, place_id, has_google_data):
            self.place_id = place_id
            self.has_google_data = has_google_data

    def __init__(self, data_chunck):
        # portion of rows that hold google_data that were parsed by the 'executor_popular_times.py'
        self.data_chunk = data_chunck
        self.session_maker = sessionmaker(bind=PlacesQuerier.engine)
        # create scraper instance
        self.supermarketmeter = SupermarketMeter()
        # start scraping
        self.scrape()

    def scrape(self):
        '''
        data chunk is a list of

        :param data_chunk:
        :return:
        '''
        # start db session for inserting new entries
        self.session = self.session_maker()
        # rows = self.data_chunk[0]
        for x, row in enumerate(self.data_chunk):
            place_id = row[0]
            google_url = row[1]
            has_google_data, current_popularity_desc, current_popularity, normal_popularity = self.supermarketmeter.get_populartimes(google_url)
            # get time of recording
            now = datetime.now()
            at_time_unix = int(time.time())
            at_time_str = now.strftime("%m/%d/%Y %H:%M:%S")
            # write to entry table if there was data obtained
            if current_popularity is not None: #current_popularity is not None and normal_popularity is not None
                entry = PlacesQuerier.Entry(
                    place_id,
                    normal_popularity,
                    current_popularity,
                    current_popularity_desc,
                    at_time_str,
                    at_time_unix
                )
                self.session.add(entry)
                print("added entry")
            '''
            UNCOMMENT FOR NOW SINCE OTHERWISE DURING THE NIGHT ALL ROWS WILL BE ON FALSE - NO GOOGLE DATA
            WILL LET IT RUN WITH THE UNCOMMENTED CODE DURING THE DAY ONCE TO GET AN IDEA WHHICH SHOPS REALLY 
            HAVE DATA IN WHICH DONT.
            '''
            if not has_google_data:
                print(f"[-] no popular times graph was found for Place id: {place_id} and url: {google_url}. Setting 'has_google_data' to False")
                # fetches the row from the PLACES table with the given place_id (get() takes the primary key which place_id is)
                target_row = self.session.query(PlacesQuerier.Places).get(place_id)
                target_row.has_google_data = False
                self.session.commit()

            if x % 1 == 0: #and x != 0
                print("session commit modulo 5")
                self.session.commit()

        self.session.commit()
        #close and clean up the firefox drivers!
        print(f'[*] cleaning up firefox')
        self.supermarketmeter.driver.quit()
        #Lets us know how many Calls we have made so far.
        print("[*] there are currently " + str(self.session.query(PlacesQuerier.Entry).count()) + " rows in the Entries table")
        self.session.close()
