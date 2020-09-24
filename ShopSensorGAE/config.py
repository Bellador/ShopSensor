import os
import sqlalchemy
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    '''
    config for APP ENGINE to access the Google Cloud Postgresql database from within
    '''
    # Step 0: Gave app engine service account (shopsensor-272815@appspot.gserviceaccount.com) permission of 'Cloud SQL Client'
    # Step 1: https://cloud.google.com/sql/docs/postgres/connect-app-engine
    # Step 2: Encountered connection error visible via 'gcloud app logs tail -s default' and the google cloud web interface
    #       Error (1): Unknown package 'pg8000'. Replaced drivername of 'postgres+pg8000' by 'postgresql'
    #       Error (2): Key error -> did not recognise 'unix_sock' as a key. Changed to 'host' for fix
    #       Error (3): In the error log there were twice '.s.PGSQL.5432' attached. Removed '.s.PGSQL.5432' from query for fix.

    SQLALCHEMY_DATABASE_URI = sqlalchemy.engine.url.URL(
                                        drivername='<ADD HERE>',
                                        username='<ADD HERE>',
                                        password='<ADD HERE>',
                                        database='<ADD HERE>',
                                        query={
                                            'host': '/cloudsql/{}'.format(
                                                '<ADD HERE>')
                                        }
                              )
    '''
    config for running the server LOCALLY but still accessing the remote Google Cloud Postgresql database
    IMPORTANT: TURN OFF ANY VPN SINCE IT IS IP ACCESS RESTRICTED!
    '''
    # SQLALCHEMY_DATABASE_URI = '<ADD HERE>://<ADD HERE>:<ADD HERE>@<ADD HERE>:<ADD HERE>/<ADD HERE>'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or '<ADD HERE RANDOM CHAR STRING>'   #34kö$_^AC
