import math
import time
import psycopg2
import concurrent.futures
from places import PlacesQuerier

'''
RUN GOOGLE PLACES POPULAR TIMES MINING AS MULTICORE PROCESS

1. FETCH ALL ROWS FROM THE PLACES DB TABLE WHERE THE COLUMN 'has_google_data' IS TRUE (DEFAULT).
2. FEED THE GOOGLE URLS TO THE WEB SCRAPER
3. PLACE THE OBTAINED DATA AS ENTRY ON TO THE ENTRY TABLE
4. IF NOTHING WAS RETURNED SET THE PLACE TABLE COLUMN 'has_google_data' TO FALSE!
This extra file is needed to execute .py as a multiprocess because:
For some reason ProcessPoolExecutor() does not always work with objects not defined in an imported module.
So you have to write your function into a different file and import the module.
'''

def conn_db():
    # for local db on cluster
    # conn = psycopg2.connect(host="localhost", port=5433, database="<ADD HERE>", user="<ADD HERE>")

    # for db on Google Cloud
    conn = psycopg2.connect(host="<ADD HERE>", port=5432, database="<ADD HERE>", user="<ADD HERE>", password="<ADD HERE>")
    return conn

def fetch_rows_w_google_data(conn):
    with conn.cursor() as cursor:
        sql = "SELECT place_id, google_url FROM PLACES WHERE has_google_data IS TRUE"
        cursor.execute(sql)
        rows = cursor.fetchall()
    return rows

if __name__ == '__main__':
    PROCESSES = 30
    iteration = 1
    while True:
        start = time.time()
        # fetch place rows from db that are known to contain google popular times data
        rows = fetch_rows_w_google_data(conn_db())
        # define row where each process starts scraping
        step = len(rows) / PROCESSES
        # round UP to ensure the number of PROCESSES
        step = math.ceil(step)
        chunks = list([rows[x:x + step] for x in range(0, len(rows), step)])

        # PlacesQuerier(chunks[0])

        #applying multiprocessing
        print('_' * 60)
        print(f"[*] starting iteration {iteration} with {PROCESSES} processes of size {step}")
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # map waits in itself for all workers to finish
            results = executor.map(PlacesQuerier, chunks)
        end = time.time()
        print(f'[*] finished iteration {iteration} in {round((end - start) / 3600, 2)} hours')
        iteration += 1

