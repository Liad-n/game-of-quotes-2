from flask_login import UserMixin

from shared import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(30)) 
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    access_level = db.Column(db.Integer, db.ForeignKey('access_levels.id'), default=0)
    favorite_quotes = db.relationship('FavoriteQuote', backref='favorite_quotes')


class FavoriteQuote(db.Model):
    __tablename__ = 'favorite_quotes'
    __table_args__ = (db.UniqueConstraint('quote_id', 'user_id'),)

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Quote(db.Model):
    __tablename__ = 'quotes'

    id = db.Column(db.Integer, primary_key=True)
    quote_caption = db.Column(db.Text, unique=True, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('characters.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Character(db.Model):
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'))
    image_url_full = db.Column(db.Text)
    image_url_thumb = db.Column(db.Text)
    quotes = db.relationship('Quote', backref='quotes')


class House(db.Model):
    __tablename__ = 'houses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    members = db.relationship('Character', backref='members')


class AccessLevel(db.Model):
    __tablename__ = 'access_levels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    members = db.relationship('User', backref='members')

