from shared import db


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(30)) 
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.Text)
    access_level = db.Column(db.Integer, default=0)
    favorite_quotes = db.relationship('FavoriteQuotes', backref='liked_by_user')


class FavoriteQuotes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Quotes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_caption = db.Column(db.Text, unique=True)
    author_id = db.Column(db.Integer, db.ForeignKey('characters.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Characters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'))
    image_url_full = db.Column(db.Text)
    image_url_thumb = db.Column(db.Text)
    quotes = db.relationship('Quotes', backref='quotes')


class Houses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    members = db.relationship('Characters', backref='members')
