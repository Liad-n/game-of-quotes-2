import random

import bcrypt
from flask import abort, redirect, render_template, request, url_for, flash, jsonify, make_response

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.functions import user


from models import AccessLevel, Character, FavoriteQuote, House, Quote, User
from shared import app, db


from flask_login import LoginManager, login_user, logout_user, current_user


# Configure flask login
login = LoginManager(app)
login.init_app(app)


@login.user_loader
def load_user(_id):
    return User.query.get(int(_id))


# Routes
@app.route('/')
def index():
    search_input = request.args.get('search')
    if not search_input:
        return render_template('index.j2', quote_obj=None)
    
    response = get_char_or_house(search_input)
    if type(response) == House:
        char = random.choice(response.members)
        quote_obj = random.choice(char.quotes)
        quote = quote_obj.quote_caption
        char_name = char.name
        img_url = char.image_url_full
    elif type(response) == Character:
        char = response
        quote_obj = random.choice(char.quotes)
        quote = quote_obj.quote_caption
        char_name = response.name
        img_url = response.image_url_full
    elif type(response) == Quote:
        quote_obj = response
        quote = response.quote_caption
        char = Character.query.filter_by(id=response.author_id).first()
        char_name = char.name
        img_url = char.image_url_full
    else:
        quote_obj = None
        char_name = 'Not Found'
        quote = 'Sadly, we found nothing to match your expectation. For you, the night is dark and full of terrors.'
        img_url = url_for('static', filename='images/no-image.jpg')

    return render_template('./index.j2', quote_obj=quote_obj, search_input=search_input, quote=quote, char_name=char_name, img_url=img_url)


@app.route('/quote/<quote_id>')
def quote_id(quote_id):
    quote_obj = Quote.query.filter_by(id=quote_id).first()
    if not quote_obj:
        flash('Oops, we did not find you the quote you were looking for. Try searching for a different one.')
        return redirect(url_for('index'))
    quote = quote_obj.quote_caption
    char = Character.query.filter_by(id=quote_obj.author_id).first()
    char_name = char.name
    img_url = char.image_url_full

    return render_template('./index.j2', quote_obj=quote_obj, quote=quote, char_name=char_name, img_url=img_url)


@app.route('/random')
def random_quote():
    quote_obj = random.choice(Quote.query.all())
    quote = quote_obj.quote_caption
    char = Character.query.filter_by(id=quote_obj.author_id).first()
    char_name = char.name
    img_url = char.image_url_full

    return render_template('./index.j2', quote_obj=quote_obj, quote=quote, char_name=char_name, img_url=img_url)


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
    user = User(**fields)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        flash(f"Username {fields['username']} already exists! Try another username.")
        return render_template('register.j2')
    flash("Success! You can now login.")
    return render_template('login.j2')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user:
            return render_template('login.j2', session=current_user)
        else:
            return render_template('login.j2')

    username = request.form['username']
    if username is None:
        return abort(400, 'You must enter a username')
    user_object = User.query.filter_by(username=username).first()
    if not user_object:
        return abort(404, 'User does not exist')
    
    password = request.form['password'].encode('utf-8')
    real_password = str(user_object.password).encode('utf-8')

    if not bcrypt.checkpw(password, real_password):
        return abort(403, 'Username and password do not match')
    
    login_user(user_object)
    if current_user.is_authenticated:
        flash(f'Logged in successfully. Welcome {current_user.full_name}.')
        return redirect(url_for('user_profile'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/admin/manage-users', methods=['GET', 'POST'])
def admin_manage_users():
    # print(AccessLevel.query.filter_by(id=current_user.access_level).first().name)
    if current_user.is_authenticated and current_user.access_level == 1:
        users_objects = User.query.all()
        # for u in users_objects:
        #     print(u.access_level_name)
        # for c in Character.query.all():
        #     print(c.quotes)
        return render_template('manage-users.j2', users=users_objects)
    else:
        return abort(403, 'Not allowed')


@app.route('/admin/delete-quote/<quote_id>', methods=['GET', 'POST'])
def admin_delete_quote(quote_id):
    if current_user.is_authenticated and current_user.access_level == 1:
        delete_quote(quote_id)
    
        return render_template('index.j2')
    else:
        return abort(403, 'Not allowed')


@app.route('/admin/add-quote', methods=['GET', 'POST'])
def admin_add_quote():
    if current_user.is_authenticated and current_user.access_level == 1:
        if request.method == 'GET':
            return render_template('add-quote.j2')
        
        caption = request.form['quote_caption']
        author_name = request.form['author_name'].lower()
        user_name = request.form['added_by'].lower()
        
        author = Character.query.filter(func.lower(Character.name).like(f'%{author_name}%')).first()
        user = User.query.filter(func.lower(User.full_name).like(f'%{user_name}%')).first()
        if author:
            author_id = author.id
        else:
            author_id = None
        if user:
            user_id = user.id
        else:
            user_id = None
        if caption and author_id:
            add_new_quote(author_id=author_id, quote_caption=caption, user_id=user_id)
        else:
            flash(message='Quote has to have a valid author and caption', category='success')
            
        return redirect(url_for('admin_add_quote'))
    else:
        return abort(403, 'Not allowed')


@app.route('/profile', methods=['GET', 'POST'])
def user_profile():
    if current_user.is_authenticated:
        query_result = FavoriteQuote.query.join(Quote).join(Character).filter(FavoriteQuote.user_id == current_user.id).add_columns(FavoriteQuote.id, Quote.quote_caption, Character.name).all()
        return render_template('user-profile.j2', user=current_user, quote_model=Quote, favorite_quotes=query_result)
    else:
        return abort(403, 'Not allowed')


@app.route('/add-favorite-quote/<action>', methods=['GET', 'POST'])
def add_favorite_quote(action):
    req = request.get_json()

    res = make_response(jsonify({'message': 'JSON received'}), 200)
    if req:
        
        quote_id = req['quote']
        if action == 'add':
            add_favorite_quote_by_id(quote_id)
        else:
            remove_favorite_quote_by_id(quote_id)

    return res


@app.route('/admin/delete-user/<user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    user_obj = User.query.get(user_id)

    if not user_obj or user_obj.access_level > 0:
        flash(message=f'Sorry, user could not be deleted.', category='error')
        return redirect(url_for('admin_manage_users'))

    username_to_delete = user_obj.username
    if current_user.is_authenticated and current_user.access_level == 1:
        delete_user_by_id(user_id)
        flash(message=f'User {username_to_delete} deleted successfully.', category='success')

        return redirect(url_for('admin_manage_users'))
    else:
        return abort(403, 'Not allowed')


def get_char_or_house(query):
    lower_query = query.lower()
    response = House.query.filter(func.lower(House.name).like(f'%{lower_query}%')).first()
    if response:
        return response
    response = Character.query.filter(func.lower(Character.name).like(f'%{lower_query}%')).first()
    if response:
        return response
    response = Quote.query.filter(func.lower(Quote.quote_caption).like(f'%{lower_query}%')).first()
    if response:
        return response


def add_new_quote(author_id, quote_caption, user_id):
    new_quote = Quote(quote_caption=quote_caption, author_id=author_id, user_id=user_id)
    if new_quote:
        db.session.add(new_quote)
        db.session.commit()
        flash(message='Quote added successfully! Thanks!', category='success')
        return True
    else:
        return False


def delete_quote(quote_id):
    # add remove from favorite quotes
    quote_to_delete = Quote.query.filter_by(id=quote_id).first()
    # print(quote_to_delete)
    if quote_to_delete:
        db.session.delete(quote_to_delete)
        db.session.commit()
        flash(message='Quote deleted successfully.', category='success')
        return True
    else:
        flash(message='Couldn\'t find the selected quote', category='error')
        return False


def add_favorite_quote_by_id(quote_id):
    if current_user.is_authenticated:
        quote = Quote.query.filter_by(id=quote_id).first()
        new_fav_quote = FavoriteQuote(user_id=current_user.id, quote_id=quote.id)
        db.session.add(new_fav_quote)
        db.session.commit()
        flash(message='Quote added successfully to favorite quotes.', category='success')


def remove_favorite_quote_by_id(quote_id):
    if current_user.is_authenticated:
        quote = Quote.query.filter_by(id=quote_id).first()
        fav_quote_to_delete = FavoriteQuote.query.filter_by(user_id=current_user.id, quote_id=quote.id).first()
        db.session.delete(fav_quote_to_delete)
        db.session.commit()


def delete_favorite_quote(quote_id):
    if current_user.is_authenticated:
        quote_to_delete = FavoriteQuote.query.filter_by(user_id=current_user.id).filter_by(quote_id=quote_id).first()
        if quote_to_delete:
            db.session.delete(quote_to_delete)
            db.session.commit()
            flash(message='Quote deleted successfully.', category='success')
        else:
            flash(message='Couldn\'t find the selected quote', category='error')


def delete_user_by_id(user_id):
    if current_user.is_authenticated and current_user.access_level == 1:
        user_to_delete = User.query.get(user_id)
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            return True
    else:
        return False


if __name__ == "__main__":
    app.run()
