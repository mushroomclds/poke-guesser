from flask import Flask
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logging
setup_logging()  # Initialize logging


import os

def create_app(config_class=Config):

    # Create Flask app instance
    app = Flask(__name__)
    app.config.from_object(config_class) # dict of attributes from Config class
    '''
    CORS (Cross-Origin Resource Sharing) is a security feature in web browsers 
    that controls which websites can make requests to your backend server.
    By enabling CORS in your Flask app, you allow your frontend (running on a 
    different address or port) to communicate with your backend API.
    '''
    # Use CORS origins from config
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['https://mushroom-clouds.com']))


    # Setup logging

    # Register blueprints (route modules)
    # from .routes.auth import auth
    from .routes.api import api

    ''' 
    Add all the routes defined in auth.py and api.py to the app
    make them available under the specified URL prefixes
    '''
    # app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(api, url_prefix="/api")

    return app
