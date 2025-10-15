from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

def make_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    return app

load_dotenv()
app = make_app()
