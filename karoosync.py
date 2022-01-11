import configparser
import json
import jwt
import requests
import os
import sys
from base64 import b64encode
from bs4 import BeautifulSoup
from datetime import datetime


def write_configfile(config, filename):
    text = r"""
[INTERVALS.ICU]
INTERVALS_ICU_ID = i00000
INTERVALS_ICU_APIKEY = 00000000000000000000

[HAMMERHEAD]
HAMMERHEAD_USERNAME = your_email_address
HAMMERHEAD_PASSWORD = your_password
"""
    with open(filename, 'w') as configfile:
        configfile.write(text)
    print(f'Created {filename}. Add your user details to that file and run karoosync again.')
    sys.exit(0)


def get_access_token(username, password):
    url = "https://dashboard.hammerhead.io/v1/auth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "grant_type": "password",
        "username": username,
        "password": password
    }
    response = call_api(url, "POST", headers=headers, payload=payload).json()
    access_token = response['access_token']
    return access_token


def get_userid(token):
    jwt_data = jwt.decode(token, algorithms="HS256", options={"verify_signature": False})
    user = jwt_data['sub']
    return user


def get_workouts(oldest, newest, user_id, api_key):
    url = f'https://intervals.icu/api/v1/athlete/{user_id}/events?oldest={oldest}&newest={newest}'

    token = b64encode(f'API_KEY:{api_key}'.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'text/plain'
    }
    workouts = call_api(url, "GET", headers).json()
    for workout in workouts:
        if workout['type'] == "Ride" and workout['start_date_local'][0:10] == newest:
            workout_id = workout['id']
            date = workout['start_date_local'][0:10]
            json_workout = {'id': workout_id, 'date': date}

    return json_workout


def get_workout(workout_id, user_id, api_key):
    url = f'https://intervals.icu/api/v1/athlete/{user_id}/events/{workout_id}/downloadzwo'

    token = b64encode(f'API_KEY:{api_key}'.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'text/plain'
    }
    response = call_api(url, "GET", headers)
    return response.text


def call_api(url, method, headers, payload=None):
    try:
        response = requests.request(method, url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print("User credentials not valid. Please correct and try again.")
        sys.exit(1)
    return response


def convert_zwo(zwo_xml, date):
    bs_data = BeautifulSoup(zwo_xml, "xml")
    steps = bs_data.find_all('SteadyState')
    # Get name from ZWO file, if no name just name it "Workout"
    name = bs_data.find('name').get_text() or 'Workout'

    list_structure = []
    power = None
    cadence = None

    for step in steps:
        duration = int(step.get('Duration'))
        if step.get('Power'):
            power = int(float(step.get('Power')) * 100)
        if step.get('Cadence'):
            cadence = int(step.get('Cadence'))

        structure = {
            "class": "active",
            "length": duration,
            "lengthType": "seconds",
            "primaryTarget": {
                "type": "percent-ftp",
                "value": power
            },
            "type": "step"
        }
        list_structure.append(structure)
        if cadence is not None:
            structure['secondaryTarget'] = {
                "type": "cadence",
                "value": cadence
            }
        cadence = None
    dict_structure = {
        "name": name,
        "source": "N/A",
        "structure": list_structure,
        "plannedDate": date
    }

    return dict_structure


def upload_workout(user, token, workout):
    url = f"https://dashboard.hammerhead.io/v1/users/{user}/workouts"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = call_api(url, "POST", headers=headers, payload=json.dumps(workout))
    return response


def main():
    # Read config file
    CONFIGFILE = 'karoosync.cfg'
    config = configparser.ConfigParser()

    config_exists = os.path.exists(CONFIGFILE)
    if config_exists:
        try:
            config.read(CONFIGFILE)
            INTERVALS_ICU_ID = config['INTERVALS.ICU']['INTERVALS_ICU_ID']
            INTERVALS_ICU_APIKEY = config['INTERVALS.ICU']['INTERVALS_ICU_APIKEY']
            HAMMERHEAD_USERNAME = config['HAMMERHEAD']['HAMMERHEAD_USERNAME']
            HAMMERHEAD_PASSWORD = config['HAMMERHEAD']['HAMMERHEAD_PASSWORD']
            # Set date to today. Might add as option in future if it makes sense.
            WORKOUT_OLDEST_DATE = datetime.today().strftime('%Y-%m-%d')
            WORKOUT_NEWEST_DATE = datetime.today().strftime('%Y-%m-%d')
        except KeyError:
            print(f'Could not read {CONFIGFILE}. Please check again.')
            sys.exit(1)
    else:
        write_configfile(config, CONFIGFILE)

    # Get Hammerhead dashboard access token
    token = get_access_token(HAMMERHEAD_USERNAME, HAMMERHEAD_PASSWORD)

    # Get user ID from JWT token
    user = get_userid(token)

    # Get list of all workouts between these dates, default = only today
    workout = get_workouts(WORKOUT_OLDEST_DATE, WORKOUT_NEWEST_DATE, INTERVALS_ICU_ID, INTERVALS_ICU_APIKEY)
    workout_id = workout['id']
    workout_date = workout['date']

    # Get ZWO file for selected workout
    workout_zwo = get_workout(workout_id, INTERVALS_ICU_ID, INTERVALS_ICU_APIKEY)

    # Convert ZWO file to Hammerhead JSON
    workout_hammerhead = convert_zwo(workout_zwo, workout_date)

    # Upload to Hammerhead
    response = upload_workout(user, token, workout_hammerhead)
    print(f'Successfully created workout {response.text.strip()}\nYou should see this workout on your Karoo device now if you are in the Workouts menu. Re-run this script if you are not, as a manual or automatic sync will delete this workout again.')


if __name__ == "__main__":
    main()
