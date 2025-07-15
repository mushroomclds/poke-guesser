# Routes package initialization
# from .api import api
# from .auth import auth

def init_routes(app):
    # app.register_blueprint(auth)
    app.register_blueprint(api)
