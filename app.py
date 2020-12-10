import random
from flask import request, render_template, redirect, abort, url_for, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from shared import app, db
from models import Users, FavoriteQuotes, Quotes, Characters, Houses
from sqlalchemy.exc import IntegrityError


@app.route('/')
def index():
    search_input = request.args.get('search')
    if not search_input:
        return render_template('index.j2')
    
    response = get_char_or_house(search_input)
    if type(response) == Houses:
        char = random.choice(response.members)
        quote = random.choice(char.quotes).quote_caption
        char_name = char.name
        img_url = char.image_url_full
    elif type(response) == Characters:
        quote = random.choice(response.quotes).quote_caption
        char_name = response.name
        img_url = response.image_url_full
    elif type(response) == Quotes:
        quote = response.quote_caption
        char = Characters.query.filter_by(id=response.author_id).first()
        char_name = char.name
        img_url = char.image_url_full
    else:
        #return abort(404, 'Sadly, we found nothing to match your expectation. \nFor you, the night is dark and full of terrors.')
        char_name = 'Not Found'
        quote = 'Sadly, we found nothing to match your expectation. For you, the night is dark and full of terrors.'
        img_url = url_for('static', filename='images/no-image.jpg')

    return render_template('./index.j2', search_input=search_input, quote=quote, char_name=char_name, img_url=img_url)


@app.route('/random')
def random_quote():
    quote_obj = random.choice(Quotes.query.all())
    quote = quote_obj.quote_caption
    char = Characters.query.filter_by(id=quote_obj.author_id).first()
    char_name = char.name
    img_url = char.image_url_full

    return render_template('./index.j2', quote=quote, char_name=char_name, img_url=img_url)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.j2')
    salt = bcrypt.gensalt(prefix=b"2b", rounds=5)
    raw_password = request.form['password'].encode('utf-8')
    hashed_password = bcrypt.hashpw(raw_password, salt)
    fields = {
        **request.form,
        'password': hashed_password.decode('utf-8'),
        }
    user = Users(**fields)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        return f"Username {fields['username']} already exists! Try another username."
    return 'Success!'
    # return render_template('./register.j2')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.j2')
    
    username = request.form['username']
    if username is None:
        return abort(400, 'You must enter a username')

    # users = Table('users', metadata, autoload=True, autoload_with=engine)
    # user = select([users]).where(Username.username == username).get()

    user = Users.query.filter_by(username=username).first()
    if not user:
        return abort(404, 'User does not exist')
    
    password = request.form['password'].encode('utf-8')
    real_password = str(user.password).encode('utf-8')

    if not bcrypt.checkpw(password, real_password):
        return abort(403, 'Username and password do not match')
    session['username'] = user.username
    session['full_name'] = user.full_name

    return redirect(url_for('user_profile'))
    # return redirect(url_for('admin_manage_users'))


@app.route('/admin/manage-users', methods=['GET', 'POST'])
def admin_manage_users():
    if session and Users.query.filter_by(username=session['username']).first().access_level == 1:
        return render_template('manage-users.j2', is_admin=1, users=Users.query.all())
    else:
        return abort(403, 'Not allowed')



@app.route('/profile', methods=['GET', 'POST'])
def user_profile():
    if session and Users.query.filter_by(username=session['username']).first():
        return render_template('user-profile.j2', user=Users.query.filter_by(username=session['username']).first())
    else:
        return abort(403, 'Not allowed')


def get_char_or_house(query):
    lower_query = query.lower()
    response = Houses.query.filter(Houses.name.like(f'%{lower_query}%')).first()
    if response:
        return response
    response = Characters.query.filter(Characters.name.like(f'%{lower_query}%')).first()
    if response:
        return response
    response = Quotes.query.filter(Quotes.quote_caption.like(f'%{lower_query}%')).first()
    if response:
        return response

def delete_favorite_quote(quote_id):
    quote_to_delete = FavoriteQuotes.query.filter_by(user_id=Users.query.filter_by(username=session['username']).first().id).filter_by(quote_id=quote_id).first()
    db.session.delete()



if __name__ == "__main__":
    app.run()
