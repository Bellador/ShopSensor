import time

from flask import render_template, request, jsonify
from sqlalchemy import text

from . import app, db
from .models import Place, Request, Observation


@app.route('/')
def startsearch():
    return render_template('app.html')

@app.route('/searchresults', methods=["POST"])
def searchresults():
    '''
    This function will be implemented in the Flask ShopSensorGAE of the Popular Times WebApp which will:
    1. Obtain search parameters from the client. For now we'll consider:
        - BBox
        - Search filter -> shop type
        - (?) Future: Currently open -> open hours
    2. Filter the Database for the passed parameters. Return all places that match and link them with the entries table
    3. Logic function ranks returned Places according to the following parameters:
        - ratio of current to normal place popularity
        - ... ?
    4. Return results to client and visualise them
    5. Log user requests on en requests table to keep track of usage load and user interest
    :return:
    '''
    current_request = request
    '''
    get debugging console output in the appengine
    '''
    # print(f"Request: {current_request}")
    # print(f"Request objects: {dir(current_request)}")
    # print(f"Remote addr: {request.remote_addr}")
    # print(f"Remote user: {request.remote_user}")
    # print(f"Truested hosts: {request.trusted_hosts}")
    # print(f"Environ: {request.environ}")
    # print(f"Acces route: {request.access_route}")
    # print(f"User agent: {request.user_agent}")
    # print(f"HTTP_X_APPENGINE_USER_IP: {request.environ['HTTP_X_APPENGINE_USER_IP']}")
    # print(f"First element access route: {request.access_route[0]}")

    # load json
    content = request.json
    bbox = content['bbox']
    '''
    Fetch and sanitise client bbox information for query
    '''
    # bbox = content["bbox"]  # contains two keys which represents the SE NW points of the bbox
    north_east_corner = bbox["_northEast"]
    south_west_corner = bbox["_southWest"]
    xmin = south_west_corner["lng"]
    ymin = south_west_corner["lat"]
    xmax = north_east_corner["lng"]
    ymax = north_east_corner["lat"]
    # (USER INPUT CONTROL 0) sanitation of potential escape strings
    chars = "'#%-;ORUNI"
    for char in chars:
        try:
            xmin = xmin.replace(char, '')
            ymin = ymin.replace(char, '')
            xmax = xmax.replace(char, '')
            ymax = ymax.replace(char, '')
        # in case the data is not a string
        except:
            pass

    '''
    Fetch and sanitise client bbox information for query
    '''
    shoptypes = content['shopTypes']
    allowed_shoptypes = ['all_shops', 'grocery_shops', 'take_aways', 'public_transport_stations', 'pharmacies', 'post_offices', 'bakeries_butcheries']

    shoptype_db_labels = {'grocery_shops': ['Migrolino', 'Coop', 'Denner', 'convenience stores', 'Spar', 'Landi', 'Migros', 'Aldi Schweiz', 'Lidl', 'Lebensmittelladen', 'supermarkets', 'Aldi', 'Volg'],
                            'take_aways': ['Dönerladen', 'takeaway shop', 'pizza shop', 'kebab shop', 'Pizzaria', 'takeaway food', 'Kiosk', 'Avec Kiosk', 'petrol station', 'Tankstelle', 'gas station'],
                            'public_transport_stations': ['tram stations', 'train stations', 'Tramstation', 'Bushaltestelle', 'Bahnhof', 'bus stations'],
                            'pharmacies': ['Apotheke', 'pharmacies'],
                            'post_offices': ['post offices', 'Post'],
                            'bakeries_butcheries': ['bakeries', 'Bäckerei', 'Metzger']
                            }

    search_shoptype_lables = []
    # means specific shoptype selection was made
    if 'all_shops' not in shoptypes:
        for shoptype in shoptypes:
            if shoptype in allowed_shoptypes:
                labels = shoptype_db_labels[shoptype]
                search_shoptype_lables = search_shoptype_lables + labels
            else:
                continue

    # call the PostGIS query to fetch places inside the bbox and corresponding entries that go back a specified time
    current_unix_time = int(time.time())  # seconds
    # records that lie a max. of here defined seconds in the past will be fetched (e.g. 1 week = 604800‬s, 1 day = 86400)
    '''Size of historical timeperiod for which popularity data is fetched'''
    timeback = 604800
    min_unix = current_unix_time - timeback
    '''
    Obtain sensor data for the bbox
    '''
    # return specified shop types
    if search_shoptype_lables:
        #see: https://stackoverflow.com/questions/10738446/postgresql-select-rows-where-column-array
        place_query = text('SELECT p.place_id, p.place_name, p.lat, p.lng, p.address, p.open_hours, p.store_url, '
                            'e.current_popularity, e.normal_popularity, e.current_popularity_desc, e.at_time_unix '
                            'FROM (SELECT * FROM places WHERE ST_MakeEnvelope (:xmin, :ymin, :xmax, :ymax, 4326) && geometry AND used_search_term = ANY(:shoptypes)) AS p '
                            'LEFT JOIN (SELECT * FROM entries WHERE at_time_unix >= :min_unix) AS e '
                            'ON p.place_id = e.place_id '
                            'ORDER BY e.at_time_unix DESC')
    # return all shop types
    else:
        place_query = text('SELECT p.place_id, p.place_name, p.lat, p.lng, p.address, p.open_hours, p.store_url, '
                           'e.current_popularity, e.normal_popularity, e.current_popularity_desc, e.at_time_unix '
                           'FROM (SELECT * FROM places WHERE ST_MakeEnvelope (:xmin, :ymin, :xmax, :ymax, 4326) && geometry) AS p '
                           'LEFT JOIN (SELECT * FROM entries WHERE at_time_unix >= :min_unix) AS e '
                           'ON p.place_id = e.place_id '
                           'ORDER BY e.at_time_unix DESC')

    # create response. Message will be crafted according to the success or failure of the request
    response_dict = {'message': 'success'}

    # (USER INPUT CONTROL 1) Check if coordinates (decimals, floats) were provided
    if isinstance(xmin, float) and isinstance(ymin, float) and isinstance(xmax, float) and isinstance(ymax, float):
        # (USER INPUT CONTROL 2) Check if extend is not bigger than allowed given the locked max zoom level +1
        bbox_extend_zoom_13 = {'north_east_corner':
                                        {
                                        "lat": 47.210706470580504,
                                        "lng": 8.698425292968752
                                        },
                                'south_west_corner':
                                        {
                                        "lat": 47.14326289171814,
                                        "lng": 8.373985290527346
                                        }
                                }
        # allowed bbox extend
        allowed_diff_x = bbox_extend_zoom_13['north_east_corner']['lng'] - bbox_extend_zoom_13['south_west_corner']['lng']
        allowed_diff_y = bbox_extend_zoom_13['north_east_corner']['lat'] - bbox_extend_zoom_13['south_west_corner']['lat']
        # request bbox extend
        request_diff_x = xmax - xmin
        request_diff_y = ymax - ymin
        # check if request bbox is in the allowed extend bounds according to the allowed zoom level
        if request_diff_x <= allowed_diff_x and request_diff_y <= allowed_diff_y:
            if search_shoptype_lables:
                rows = db.engine.execute(place_query,
                                         xmin=xmin,
                                         ymin=ymin,
                                         xmax=xmax,
                                         ymax=ymax,
                                         shoptypes=search_shoptype_lables,
                                         min_unix=min_unix).fetchall()
            else:
                rows = db.engine.execute(place_query,
                                         xmin=xmin,
                                         ymin=ymin,
                                         xmax=xmax,
                                         ymax=ymax,
                                         min_unix=min_unix).fetchall()
            # check if not empty
            if rows:
                place_id_idx = 0
                place_name_idx = 1
                lat_idx = 2
                lng_idx = 3
                address_idx = 4
                open_hours_idx = 5
                store_url_idx = 6
                current_popularity_idx = 7
                normal_popularity_idx = 8
                current_popularity_desc_idx = 9
                at_time_unix_idx = 10
                # ranks = []  # tuples containing place_id and most recent current / normal popularity ratio

                places_w_sensordata = 0
                # only places with sensor data not older than specified will be used for the ranking!
                max_age_sensors = 3600 # 1h

                for row in rows:
                    place_id = row[place_id_idx]
                    current_popularity = row[current_popularity_idx]
                    normal_popularity = row[normal_popularity_idx]
                    # check if there is sensor data
                    if current_popularity is not None and normal_popularity is not None:
                        # means that the this is the most recent entry for that place
                        if place_id not in response_dict.keys():
                            places_w_sensordata += 1
                            '''
                            Check of the current popularity is up-to-date given the max_age_sensor
                            '''
                            current_time_sensor = row[at_time_unix_idx]
                            time_back_sensor = current_unix_time - current_time_sensor
                            if time_back_sensor <= max_age_sensors:
                                # rank is build of the current popularity times the ratio between the curr pop and the normal pop for that time
                                # calculate the current popularity to normal popularity ratio for each place (for the ranking)
                                try:
                                    if normal_popularity != 0:
                                        ratio = current_popularity / normal_popularity  # the SMALLER the better
                                    else:
                                        ratio = current_popularity
                                    # ranks.append((place_id, ratio * current_popularity))
                                    sensor_rank = ratio * current_popularity
                                except:
                                    # a place where no popularity data exists because it gets a None object
                                    ratio = 'NoData'
                                    sensor_rank = None
                            else:
                                sensor_rank = None
                                ratio = 'NoData'
                            '''
                            Handle missing data
                            '''
                            if row[address_idx] is not None:
                                address = row[address_idx]
                            else:
                                address = 'NoData'
                            if row[open_hours_idx] is not None:
                                open_hours = row[open_hours_idx].split(',')
                            else:
                                open_hours = 'NoData'
                            if row[store_url_idx] is not None:
                                store_url = row[store_url_idx]
                            else:
                                store_url = '#'

                            response_dict[place_id] = {
                                'popularity_rank': None,
                                'place_name': row[place_name_idx],
                                'lat': row[lat_idx],
                                'lng': row[lng_idx],
                                'address': address,
                                'open_hours': open_hours,
                                'store_url': store_url,
                                'popular_times': {
                                    'sensor_rank': sensor_rank,
                                    'most_recent': {
                                        'ratio': ratio,
                                        'current': row[current_popularity_idx],
                                        'normal': row[normal_popularity_idx],
                                        'desc': row[current_popularity_desc_idx],
                                        'unix_time': row[at_time_unix_idx]
                                    },
                                    'historical': []
                                    # list of dictionaries identical to most_recent which hold records with increasing age
                                }
                            }
                        # means that this row contains historical popular time data for that place
                        else:
                            historical_record = {
                                'ratio': ratio,
                                'current': row[current_popularity_idx],
                                'normal': row[normal_popularity_idx],
                                'desc': row[current_popularity_desc_idx],
                                'unix_time': row[at_time_unix_idx]
                            }
                            response_dict[place_id]['popular_times']['historical'].append(historical_record)
                    # simply add the place if no sensor data is present
                    else:
                        # check to not overwrite entries
                        if place_id not in response_dict.keys():
                            '''
                            Handle missing data
                            '''
                            if row[address_idx] is not None:
                                address = row[address_idx]
                            else:
                                address = 'NoData'
                            if row[open_hours_idx] is not None:
                                open_hours = row[open_hours_idx].split(',')
                            else:
                                open_hours = 'NoData'
                            if row[store_url_idx] is not None:
                                store_url = row[store_url_idx]
                            else:
                                store_url = '#'

                            response_dict[place_id] = {
                                'popularity_rank': None,
                                'place_name': row[place_name_idx],
                                'lat': row[lat_idx],
                                'lng': row[lng_idx],
                                'address': address,
                                'open_hours': open_hours,
                                'store_url': store_url
                            }
                # for the query statistics
                response_dict['statistic'] = {}
                response_dict['statistic']['places_w_sensordata'] = places_w_sensordata
                # from all places find the one with lowest calculated popularity ratio
                '''
                rank placement
                '''
                # ranks.sort(key=lambda x: x[1])
                # for rank, tuple_ in enumerate(ranks, 1):
                #     place_id = tuple_[0]
                #     response_dict[place_id]['popularity_rank'] = rank

            '''
            Obtain observation data for the bbox
            '''
            if search_shoptype_lables:
                observation_data_query = text('SELECT p.place_id, '
                                              'o.prediction_people, o.prediction_queue, o.at_time_unix '
                                              'FROM (SELECT * FROM places WHERE ST_MakeEnvelope (:xmin, :ymin, :xmax, :ymax, 4326) && geometry AND used_search_term = ANY(:shoptypes)) AS p '
                                              'LEFT JOIN (SELECT * FROM observations) AS o ' #WHERE at_time_unix >= :min_unix
                                              'ON p.place_id = o.place_id '
                                              'ORDER BY o.at_time_unix DESC')
                rows = db.engine.execute(observation_data_query,
                                         xmin=xmin,
                                         ymin=ymin,
                                         xmax=xmax,
                                         ymax=ymax,
                                         shoptypes=search_shoptype_lables,
                                         min_unix=min_unix).fetchall()
            else:
                observation_data_query = text('SELECT p.place_id, '
                                              'o.prediction_people, o.prediction_queue, o.at_time_unix '
                                              'FROM (SELECT * FROM places WHERE ST_MakeEnvelope (:xmin, :ymin, :xmax, :ymax, 4326) && geometry) AS p '
                                              'LEFT JOIN (SELECT * FROM observations) AS o ' #WHERE at_time_unix >= :min_unix
                                              'ON p.place_id = o.place_id '
                                              'ORDER BY o.at_time_unix DESC')
                rows = db.engine.execute(observation_data_query,
                                         xmin=xmin,
                                         ymin=ymin,
                                         xmax=xmax,
                                         ymax=ymax,
                                         min_unix=min_unix).fetchall()
            if rows:
                place_id_idx = 0
                prediction_people_idx = 1
                prediction_queue_idx = 2
                at_time_unix_idx = 3

                nr_of_observations = 0

                for row in rows:
                    place_id = row[place_id_idx]
                    prediction_people = row[prediction_people_idx]
                    prediction_queue = row[prediction_queue_idx]
                    at_time_unix = row[at_time_unix_idx]
                    # check if there is any observation data (not None)
                    if prediction_people is not None and prediction_queue is not None:
                        nr_of_observations += 1
                        # check if for most recent observation for a given place (first row for every place) by checking if key 'observation_data' exists
                        if 'observation_data' not in response_dict[place_id].keys():
                            # craft new entry in response
                            response_dict[place_id]['observation_data'] = {}
                            response_dict[place_id]['observation_data']['most_recent'] = {
                                'prediction_people': prediction_people,
                                'prediction_queue': prediction_queue,
                                'unix_time': at_time_unix
                            }
                            # create historical key with list
                            response_dict[place_id]['observation_data']['historical'] = []
                            '''
                            potential observation rank calculation for the most recent observation
                            '''
                            # calculate the difference between the current time and when the observation was made
                            time_back_observation = current_unix_time - at_time_unix
                            # defines how old (in seconds) an observation can be to be used for ranking
                            max_age_observations = 3600  # 1h
                            if time_back_observation <= max_age_observations:
                                observation_rank = 0
                                # calculate points
                                if prediction_people == 'few':
                                    observation_rank += 0
                                elif prediction_people == 'some':
                                    observation_rank += 50
                                # prediction_people = 'many'
                                else:
                                    observation_rank += 100

                                if prediction_queue == 'yes':
                                    observation_rank += 100
                                # prediction_queue = 'no':
                                else:
                                    observation_rank += 0

                                response_dict[place_id]['observation_data']['observation_rank'] = observation_rank

                        else:
                            historical_observation = {
                                'prediction_people': prediction_people,
                                'prediction_queue': prediction_queue,
                                'unix_time': at_time_unix
                            }
                            response_dict[place_id]['observation_data']['historical'].append(historical_observation)

                # add nr observations for the given query
                response_dict['statistic']['nr_of_observations'] = nr_of_observations
            '''
            rank placement out of sensor and observation portion
            '''
            ranks = [] # contains tuple of place_id and absolute rank
            # places that have current observations get through their trustworthiness a deduction to boost the place
            observation_bonus = 5
            for k, v in response_dict.items():
                if k != 'message' and k != 'statistic':
                    place_id = k
                    has_sensor_rank = False
                    has_observation_rank = False
                    '''
                    default sensor rank if none is given
                    '''
                    sensor_rank = 0
                    '''
                    default observation rank if none is given
                    '''
                    observation_rank = 50
                    # check for sensor data
                    if 'popular_times' in v:
                        if 'sensor_rank' in v['popular_times']:
                            # sensor rank equal none means that there is sensor data but no up-to-date one
                            if v['popular_times']['sensor_rank'] != None:
                                has_sensor_rank = True
                                sensor_rank = v['popular_times']['sensor_rank']
                    # check for observation data
                    if 'observation_data' in v:
                        if 'observation_rank' in v['observation_data']:
                            has_observation_rank = True
                            observation_rank = v['observation_data']['observation_rank'] - observation_bonus
                    '''
                    if no sensor and observation data than rank is max. (shops with no data at all)
                    '''
                    if has_sensor_rank or has_observation_rank:
                        rank = sensor_rank + observation_rank
                        ranks.append((place_id, rank))
            '''
            insert absolute rank to the appropriate places in the result dict
            '''
            ranks.sort(key=lambda x: x[1])
            for rank, tuple_ in enumerate(ranks, 1):
                place_id = tuple_[0]
                response_dict[place_id]['popularity_rank'] = rank
        # here if input covers extend larger than allowed
        else:
            print("Potentially crafted user input detected - [BBOX EXTEND]")
            response_dict['message'] = 'invalid input detected [BBOX EXTEND]'
            return response_dict
    # here if input was no float
    else:
        print("Potentially crafted user input detected - [DATA FORMAT]")
        response_dict['message'] = 'invalid input detected [DATA FORMAT]'
        return response_dict

    '''
    Craft request log entry
    '''
    # get client ip from Google App Engine specific request header
    try:
        client_ip = request.environ['HTTP_X_APPENGINE_USER_IP']
        # print(f"Client IP: {client_ip}")
    except Exception as e:
        print(f"Client IP Error: {e}")
        try:
            client_ip = request.access_route[0]
        except:
            client_ip = "untrackable"

    # write request to requests table to keep log
    request_log = Request(
        bbox=str(xmin)+','+str(ymin)+','+str(xmax)+','+str(ymax),
        search_params=None, # for now
        endpoint=request.endpoint,
        client_ip=client_ip,
        client_browser=request.user_agent.browser,
        client_os=request.user_agent.platform,
        client_language=request.headers.environ['HTTP_ACCEPT_LANGUAGE'],
        status=response_dict['message'],
        at_time_unix=int(time.time())
    )
    db.session.add(request_log)
    db.session.commit()
    # convert the python dictionary back into a json object that can be sent to the client
    json = jsonify(response_dict)
    return json

@app.route('/observation', methods=['POST'])
def observation():
    # print(f"Observation request: {request}")

    # configurations
    allowed_values_people = ['few', 'some', 'many']
    allowed_values_queue = ['yes', 'no']
    time_between_observations = 5 #minutes #doesn't work with the ip retrieval -> thats why 0
    allowed_time_diff = time_between_observations * 60
    current_unix_time = int(time.time())
    allowed_time = current_unix_time - allowed_time_diff
    # check if client has made a request in a defined previous timespan
    # get client ip from Google App Engine specific request header
    try:
        client_ip = request.environ['HTTP_X_APPENGINE_USER_IP']
        print(f"Observation Client IP: {client_ip}")
    except Exception as e:
        print(f"Client IP Error: {e}")
        try:
            client_ip = request.access_route[0]
        except:
            client_ip = "untrackable"

    ip_query = text('SELECT client_ip, at_time_unix '
                      'FROM observations '
                      'WHERE at_time_unix > :allowed_time AND client_ip = :client_ip '
                      'ORDER BY at_time_unix DESC')
    rows = db.engine.execute(ip_query,
                             allowed_time=allowed_time,
                             client_ip=client_ip).fetchall()

    # check if any matches were returned
    if not rows:
        # read client content
        content = request.json
        prediction_people = str(content['prediction_people'])
        prediction_queue = str(content['prediction_queue'])
        # check user input of radio buttons
        if prediction_people not in allowed_values_people or prediction_queue not in allowed_values_queue:
            response_dict = {"message": "Invalid parameters"}
            json = jsonify(response_dict)
            return json
        # get the time when the observation was submitted
        current_time = int(time.time())
        # check what place_id was passed with the request, check if not tempered with
        place_id = content['place_id']
        # create observation db entry
        observation_entry = Observation(
            prediction_people=prediction_people,
            prediction_queue=prediction_queue,
            at_time_unix=current_time,
            client_ip=client_ip,
            place_id=place_id
            )
        db.session.add(observation_entry)
        db.session.commit()
        response_dict = {"message": "success"}
    else:
        last_observation = rows[0][1] # returns at_time_unix of most recent observation
        try:
            time_to_wait = int((allowed_time_diff - (current_unix_time - last_observation)) / 60) #minutes
        except:
            time_to_wait = time_between_observations
        response_dict = {"message": "fail",
                         "time_to_wait": time_to_wait}
    json = jsonify(response_dict)
    return json
