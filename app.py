import os
import random

from flask import Flask, json, render_template, request
import requests


class NonExistentCharacterError(Exception):
    pass


class NonExistentHouseError(Exception):
    pass


class ApiUnavailableError(Exception):
    pass


class NoAvailableImageFoundError(Exception):
    pass


app = Flask(__name__)


@app.route('/')
def index():
    search_input = request.args.get('search')
    if not search_input:
        return render_template('index.html')
    try:
        char_quote, full_name = get_quote_by_char_or_house(search_input)
    except NonExistentCharacterError:
        char_quote, full_name = 'Not found', ''

    pictures_json = get_pictures_json()
    try:
        image_url = get_char_image_url(pictures_json, full_name)
    except NoAvailableImageFoundError:
        image_url = os.path.join(app.static_folder, 'images/no-image.jpg')

    return render_template('./index.j2', search_input=search_input, quote=char_quote, char_name=full_name, img_url=image_url)


@app.route('/<char_slug>')
def quote_page(char_slug):
    try:
        char_quote, full_name = get_quote_by_slug(char_slug)
    except NonExistentCharacterError:
        char_quote, full_name = 'Not found', ''

    pictures_json = get_pictures_json()
    try:
        image_url = get_char_image_url(pictures_json, full_name)
    except NoAvailableImageFoundError:
        image_url = os.path.join(app.static_folder, 'images/no-image.jpg')

    return render_template('./index.j2', search_input=full_name, quote=char_quote, char_name=full_name, img_url=image_url)


@app.route('/random')
def random_quote():
    try:
        char_quote, full_name = get_random_quote()
    except NonExistentCharacterError:
        char_quote, full_name = 'Not found', ''

    pictures_json = get_pictures_json()
    try:
        image_url = get_char_image_url(pictures_json, full_name)
    except NoAvailableImageFoundError:
        image_url = os.path.join(app.static_folder, 'images/no-image.jpg')

    return render_template('./index.j2', quote=char_quote, char_name=full_name, img_url=image_url)


# https://github.com/jeffreylancaster/game-of-thrones/blob/master/data/characters.json
base_api = "https://game-of-thrones-quotes.herokuapp.com/v1"


def get_characters():
    response = requests.get(f'{base_api}/characters')

    if (response.status_code == 200) and response.content:
        json_response = response.json()
        return {char['name'].lower(): char['slug'] for char in json_response}
    raise ApiUnavailableError('could not get a valid response from the api')


def get_slug_by_name(char_name):
    chars = get_characters()

    for full_name, slug in chars.items():
        if char_name in full_name:
            return slug
    return None


def get_random_quote():
    response = requests.get(f'{base_api}/random')

    if (response.status_code == 200) and response.content:
        json_response = response.json()
        quote = json_response['sentence']
        full_name = json_response['character']['name']
        return (quote, full_name)
    else:
        raise NonExistentCharacterError(f'is not a character in the api')


def get_quote_by_slug(char_name):
    response = requests.get(f'{base_api}/author/{char_name}/1')

    if (response.status_code == 200) and response.content:
        json_response = response.json()
        quote = json_response['sentence']
        full_name = json_response['character']['name']
        return (quote, full_name)
    else:
        raise NonExistentCharacterError(
            '{char_name} is not a character in the api')


def get_houses_and_members():
    response = requests.get(f'{base_api}/houses')

    if (response.status_code == 200):
        json_houses = response.json()
        houses_and_members = {house['slug']: [member['slug']
                                              for member in house['members']] for house in json_houses}

        return houses_and_members


def get_random_character_by_house_name(house_name):
    # character_name = ''
    response = requests.get(f'{base_api}/house/{house_name}')

    if (response.status_code == 200):
        json_house = response.json()
        if len(json_house) >= 1:
            members = [member['slug'] for member in json_house[0]['members']]
            character_name = random.choice(members)
            return character_name
    return ''


def get_quote_by_char_or_house(received_text):
    lower_text = received_text.lower()
    houses_and_members = get_houses_and_members()
    is_house = received_text in houses_and_members
    if is_house:
        char_name = get_random_character_by_house_name(lower_text)
    else:
        char_name = get_slug_by_name(lower_text)

    quote = get_quote_by_slug(char_name)
    return quote


def get_pictures_json():
    pictures_json = None
    response = requests.get(
        'https://raw.githubusercontent.com/jeffreylancaster/game-of-thrones/master/data/characters.json')
    if response.status_code == 200 and response.content:
        pictures_json = response.json()['characters']
    else:
        local_json = os.path.join(app.static_folder, 'characters.json')
        with open(local_json, 'r', encoding='utf-8') as fh:
            pictures_json = json.load(fh)['characters']

    return pictures_json


def get_first_name(full_name):
    return full_name.lower().split(" ")[0]


def get_last_name(full_name):
    return full_name.lower().split(" ")[-1]


def get_char_image_url(pictures_json, full_char_name):
    char_first_name = get_first_name(full_char_name)
    char_last_name = get_last_name(full_char_name)
    for json_char in pictures_json:
        json_char_first_name = get_first_name(json_char['characterName'])
        if full_char_name.lower() == json_char['characterName'].lower():
            return json_char.get('characterImageFull', '')
        elif char_first_name == json_char_first_name:
            house_name = json_char.get("houseName", "")

            if isinstance(house_name, str) and f'{char_first_name} {char_last_name}'.lower() == f"{char_first_name} {json_char.get('houseName', '').lower()}":
                return json_char.get('characterImageFull', '')
    raise NoAvailableImageFoundError(f"no image matches {full_char_name}")


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
