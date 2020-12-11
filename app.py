import random

import bcrypt
from flask import abort, redirect, render_template, request, session, url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import Characters, FavoriteQuotes, Houses, Quotes, Users
from shared import app, db


@app.route('/')
def index():
    search_input = request.args.get('search')
    if not search_input:
        return render_template('index.j2')
    
    response = get_char_or_house(search_input)
    if type(response) == Houses:
        char = random.choice(response.members)
        quote = random.choice(char.quotes)
        char_name = char.name
        img_url = char.image_url_full
    elif type(response) == Characters:
        char = response
        quote = random.choice(char.quotes)
        char_name = response.name
        img_url = response.image_url_full
    elif type(response) == Quotes:
        quote = response
        char = Characters.query.filter_by(id=response.author_id).first()
        char_name = char.name
        img_url = char.image_url_full
    else:
        char_name = 'Not Found'
        quote = 'Sadly, we found nothing to match your expectation. For you, the night is dark and full of terrors.'
        img_url = url_for('static', filename='images/no-image.jpg')

    return render_template('./index.j2', search_input=search_input, quote=quote.quote_caption, char_name=char_name, img_url=img_url)


@app.route('/quote/<quote_id>')
def quote_id(quote_id):
    quote_obj = Quotes.query.filter_by(id=quote_id).first()
    if not quote_obj:
        return redirect(url_for('index'))
    quote = quote_obj.quote_caption
    char = Characters.query.filter_by(id=quote_obj.author_id).first()
    char_name = char.name
    img_url = char.image_url_full

    return render_template('./index.j2', quote=quote, char_name=char_name, img_url=img_url)


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if get_currently_signed_in_user():
            currently_logged_in = get_currently_signed_in_user()
            return render_template('login.j2', session=currently_logged_in)
        else:
            return render_template('login.j2')
            # return render_template('user-profile.j2', user=Users.query.filter_by(username=session['username']).first())
    
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
    if get_currently_signed_in_user().access_level == 1:
        return render_template('manage-users.j2', is_admin=1, users=Users.query.all())
    else:
        return abort(403, 'Not allowed')


@app.route('/admin/delete-quote/<quote_id>', methods=['GET', 'POST'])
def admin_delete_quote(quote_id):
    if get_currently_signed_in_user().access_level == 1:
        result = delete_quote(quote_id)
        if result:
            print('Deleted successfully!')
        else:
            print('Could not find the quote')
        return render_template('manage-users.j2', is_admin=1, users=Users.query.all())
    else:
        return abort(403, 'Not allowed')


@app.route('/admin/add-quote', methods=['GET', 'POST'])
def admin_add_quote():
    if get_currently_signed_in_user().access_level == 1:
        if request.method == 'GET':
            return render_template('add-quote.j2')
        
        caption = request.form['quote_caption']
        author_name = request.form['author_name'].lower()
        user_name = request.form['added_by'].lower()
        
        author_id = Characters.query.filter(func.lower(Characters.name).like(f'%{author_name}%')).first().id
        user_id = Users.query.filter(func.lower(Users.full_name).like(f'%{user_name}%')).first().id or None
        # if caption and author_id:
        result = add_new_quote(author_id=author_id, quote_caption=caption, user_id=user_id)
        # else:
            # result = None
        if result:
            print('Added successfully!')
        else:
            print('Quote addition failed.')
        return redirect(url_for('index'))
    else:
        return abort(403, 'Not allowed')


@app.route('/profile', methods=['GET', 'POST'])
def user_profile():
    if get_currently_signed_in_user():
        return render_template('user-profile.j2', user=get_currently_signed_in_user())
    else:
        return abort(403, 'Not allowed')


# @app.route('/addquote', methods=['GET', 'POST'])
# def add_favorite_quote():
#     return render_template('index.j2', user=Users.query.filter_by(username=session['username']).first(), quote_to_add)
#     return abort(403, 'Not allowed')


def get_char_or_house(query):
    lower_query = query.lower()
    response = Houses.query.filter(func.lower(Houses.name).like(f'%{lower_query}%')).first()
    if response:
        return response
    response = Characters.query.filter(func.lower(Characters.name).like(f'%{lower_query}%')).first()
    if response:
        return response
    response = Quotes.query.filter(func.lower(Quotes.quote_caption).like(f'%{lower_query}%')).first()
    if response:
        return response


def get_currently_signed_in_user():
    if session:
        return Users.query.filter_by(username=session['username']).first()
    else:
        return None


def add_new_quote(author_id, quote_caption, user_id):
    new_quote = Quotes(quote_caption=quote_caption, author_id=author_id, user_id=user_id)
    if new_quote:
        db.session.add(new_quote)
        db.session.commit()
        return True
    else:
        return False


def delete_quote(quote_id):
    # add remove from favorite quotes
    quote_to_delete = Quotes.query.filter_by(id=quote_id).first()
    # print(quote_to_delete)
    if quote_to_delete:
        db.session.delete(quote_to_delete)
        db.session.commit()
        return True
    else:
        return False


def add_favorite_quote_by_id(quote_id):
    quote = Quotes.query.filter_by(id=quote_id).first()
    signed_in_user = get_currently_signed_in_user()
    new_fav_quote = FavoriteQuotes(user_id=signed_in_user.id, quote_id=quote.id)
    db.session.add(new_fav_quote)



def delete_favorite_quote(quote_id):
    quote_to_delete = FavoriteQuotes.query.filter_by(user_id=get_currently_signed_in_user().id).filter_by(quote_id=quote_id).first()
    db.session.delete(quote_to_delete)


if __name__ == "__main__":
    app.run()
