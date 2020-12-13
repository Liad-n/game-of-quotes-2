import json
import os

import requests
from sqlalchemy.inspection import inspect

from models import AccessLevel, Character, FavoriteQuote, House, Quote, User
from shared import app, db


def get_houses():
    response = requests.get(f'{base_api}/houses')

    if (response.status_code == 200) and response.content:
        json_response = response.json()
        return [house['name'] for house in json_response]


def get_pictures_json():
    pictures_json = None
    response = requests.get('https://raw.githubusercontent.com/jeffreylancaster/game-of-thrones/master/data/characters.json')
    if response.status_code == 200 and response.content:
        pictures_json = response.json()['characters']
    else:
        local_json = os.path.join(app.static_folder, 'characters.json')
        with open(local_json, 'r', encoding='utf-8') as fh:
            pictures_json = json.load(fh)['characters']

    return pictures_json


def get_characters():
    response = requests.get(f'{base_api}/characters')

    if (response.status_code == 200) and response.content:
        json_response = response.json()
        return json_response


def get_chars_with_pics(chars, pictures_json):
    chars_with_pics = []
    for char in chars:
        for pic_char in pictures_json:
            if (char['name'] == pic_char['characterName'] 
                or ('Brienne' in char['name'] and 'Brienne' in pic_char['characterName']) 
                or ('Eddard' in char['name'] and 'Eddard' in pic_char['characterName'])
                or ('Tormund' in char['name'] and 'Tormund' in pic_char['characterName'])
                or ('Ramsay' in char['name'] and 'Ramsay' in pic_char['characterName'])):
                char_with_pic = {'name': pic_char['characterName'], 
                                'quote_name': char['name'], 
                                'house': char.get('house', None), 
                                'image_url_full': pic_char['characterImageFull'], 
                                'image_url_thumb': pic_char['characterImageThumb'], 
                                'quotes': char['quotes']}
                chars_with_pics.append(char_with_pic)
    for char in chars_with_pics:
        if char['house'] is not None:
            char['house'] = char['house']['name']
    return chars_with_pics


def get_house_ids():
    houses = House.query.all()
    return {house.name: house.id for house in houses}


def get_chars_with_pics_and_house_ids(chars_with_pics, house_lut):
    for char in chars_with_pics:
        if char['house'] is not None:
            char['house_id'] = house_lut[char['house']]
    return chars_with_pics


def get_chars_for_table(chars, columns):
    chars_for_table = []
    for char in chars:
        new_char = {}
        for k, v in char.items():
            if k in columns:
                new_char[k] = v
        chars_for_table.append(new_char)
    return chars_for_table


def get_all_table_columns(model):
    table = inspect(model)
    return [column.name for column in table.c]


def occupy_houses():
    houses = get_houses()
    for house in houses:
        new_house = House(name=house)
        db.session.add(new_house)
    db.session.commit()


def get_chars_from_table():
    chars = Character.query.all()
    return chars


def occupy_quotes(chars_raw):
    for char in chars_raw:
        char_id = Character.query.filter_by(name=char['name']).first().id
        for quote in char['quotes']:
            new_quote = Quote(quote_caption=quote, author_id=char_id)
            db.session.add(new_quote)
    db.session.commit()


def occupy_access_levels(access_levels_map):
    db.session.bulk_insert_mappings(AccessLevel, access_levels_map)
    db.session.commit()


base_api = "https://game-of-thrones-quotes.herokuapp.com/v1"

db.create_all()

occupy_houses()

house_lut = get_house_ids()
chars = get_characters()

pictures_json = get_pictures_json()
chars_with_pics = get_chars_with_pics(chars, pictures_json)

chars_raw = get_chars_with_pics_and_house_ids(chars_with_pics, house_lut)

chars_cols = get_all_table_columns(Character)
chars_for_table = get_chars_for_table(chars_raw, chars_cols)
db.session.bulk_insert_mappings(Character, chars_for_table)
db.session.commit()

occupy_quotes(chars_raw)

access_level_values = [{'id': 0, 'name': 'User'},
                        {'id': 1, 'name': 'Admin'}]

occupy_access_levels(access_level_values)