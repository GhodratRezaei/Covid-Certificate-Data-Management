from flask import Flask

from .main.routes import main
from .extensions import mongo

def create_app():
    app = Flask(__name__)

    try:
        file = open('connection_string.txt')
        app.config['MONGO_URI'] =  file.read().strip()
        mongo.init_app(app)
    except:
        print("Connection string file not found or connection failed.")
        exit(0)

    app.register_blueprint(main)

    return app
