from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gameofquotes14.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ("DATABASE_URL")
app.config['SECRET_KEY'] = os.environ("SECRET_KEY")
# app.config.from_pyfile('config.py')
db = SQLAlchemy(app)