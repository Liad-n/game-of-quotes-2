from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gameofquotes4.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    password = db.Column(db.String(20))
    favorite_quotes = db.relationship('FavoriteQuote', backref='owner')


class FavoriteQuote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))