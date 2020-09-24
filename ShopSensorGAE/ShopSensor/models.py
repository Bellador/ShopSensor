from datetime import datetime

from . import db


class Place(db.Model):
    __tablename__ = 'places'

    place_id = db.Column(db.String(), primary_key=True)
    place_name = db.Column(db.String())
    address = db.Column(db.String())
    zip_code = db.Column(db.Integer())
    lat = db.Column(db.Float())
    lng = db.Column(db.Float())
    phone_nr = db.Column(db.String())
    open_hours = db.Column(db.String())
    rating = db.Column(db.Integer())
    store_url = db.Column(db.String())
    google_url = db.Column(db.String())
    related_terms = db.Column(db.String())
    used_search_term = db.Column(db.String())
    has_google_data = db.Column(db.Boolean())

    def __init__(self, url, result_all, result_no_stop_words):
        self.url = url
        self.result_all = result_all
        self.result_no_stop_words = result_no_stop_words

    def __repr__(self):
        return '<id {}>'.format(self.id)

class Entry(db.Model):
    __tablename__ = 'entries'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.String)  # not primary key since there will be multiple entries per place id!
    normal_popularity = db.Column(db.Integer)
    current_popularity = db.Column(db.Integer)
    current_popularity_desc = db.Column(db.String)
    at_time_str = db.Column(db.DateTime, default=datetime.now)
    at_time_UNIX = db.Column(db.Integer)

    def __init__(self, place_id, normal_popularity, current_popularity, current_popularity_desc, at_time_str,
                 at_time_UNIX):
        self.place_id = place_id
        self.normal_popularity = normal_popularity
        self.current_popularity = current_popularity
        self.current_popularity_desc = current_popularity_desc
        self.at_time_str = at_time_str
        self.at_time_UNIX = at_time_UNIX

class Request(db.Model):
    __tablename__ = 'requests'
    __table_args__ = {'extend_existing': True}
    request_id = db.Column(db.Integer, primary_key=True)
    bbox = db.Column(db.String)
    search_params = db.Column(db.String)
    endpoint = db.Column(db.String)
    client_ip = db.Column(db.String)
    client_browser = db.Column(db.String)
    client_os = db.Column(db.String)
    client_language = db.Column(db.String)
    status = db.Column(db.String)
    at_time_unix = db.Column(db.Integer)

    def __init__(self, bbox, search_params, endpoint, client_ip, client_browser, client_os, client_language, status, at_time_unix):
        self.bbox = bbox
        self.search_params = search_params
        self.endpoint = endpoint
        self.client_ip = client_ip
        self.client_browser = client_browser
        self.client_os = client_os
        self.client_language = client_language
        self.status = status
        self.at_time_unix = at_time_unix

class Observation(db.Model):
    __tablename__ = 'observations'
    __table_args__ = {'extend_existing': True}
    observation_id = db.Column(db.Integer, primary_key=True)
    prediction_people = db.Column(db.String)
    prediction_queue = db.Column(db.String)
    at_time_unix = db.Column(db.Integer)
    client_ip = db.Column(db.String)
    place_id = db.Column(db.String, db.ForeignKey('places.place_id'))

    def __init__(self, prediction_people, prediction_queue, at_time_unix, client_ip, place_id):
        self.prediction_people = prediction_people
        self.prediction_queue = prediction_queue
        self.at_time_unix = at_time_unix
        self.client_ip = client_ip
        self.place_id = place_id
