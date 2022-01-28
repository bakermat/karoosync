import configparser
import jwt
import requests
import os
import sys
import re
from base64 import b64encode


def write_configfile(filename):
    text = r"""
[INTERVALS.ICU]
INTERVALS_ICU_ID = i00000
INTERVALS_ICU_APIKEY = 00000000000000000000
# Date or date range of intervals you want to upload to your Karoo device
WORKOUT_OLDEST_DATE = 2022-01-01
WORKOUT_NEWEST_DATE = 2022-12-31

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

    list_workouts = []
    for workout in workouts:
        if workout['type'] == 'Ride':
            workout_id = workout['id']
            date = workout['start_date_local'][0:10]
            name = workout['name']
            json_workout = {'id': workout_id, 'date': date, 'name': name}
            list_workouts.append(json_workout)

    return list_workouts


def get_workout(workout_id, user_id, api_key):
    url = f'https://intervals.icu/api/v1/athlete/{user_id}/events/{workout_id}/downloadzwo'

    token = b64encode(f'API_KEY:{api_key}'.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'text/plain'
    }
    response = call_api(url, "GET", headers)
    return response.text


def call_api(url, method, headers, payload=None, files=None):
    try:
        response = requests.request(method, url, headers=headers, data=payload, files=files)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f'Something went wrong: {response.text}')
        sys.exit(1)
    return response


def upload_workout(user, token, workout):
    url = f"https://dashboard.hammerhead.io/v1/users/{user}/workouts/import/file"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = call_api(url, "POST", headers=headers, files=workout)
    return response


def main():
    # Read config file
    CONFIGFILE = 'karoosync.cfg'
    config = configparser.ConfigParser(interpolation=None)

    config_exists = os.path.exists(CONFIGFILE)
    if config_exists:
        try:
            config.read(CONFIGFILE)
            WORKOUT_OLDEST_DATE = config['INTERVALS.ICU']['WORKOUT_OLDEST_DATE']
            WORKOUT_NEWEST_DATE = config['INTERVALS.ICU']['WORKOUT_NEWEST_DATE']
            INTERVALS_ICU_ID = config['INTERVALS.ICU']['INTERVALS_ICU_ID']
            INTERVALS_ICU_APIKEY = config['INTERVALS.ICU']['INTERVALS_ICU_APIKEY']
            HAMMERHEAD_USERNAME = config['HAMMERHEAD']['HAMMERHEAD_USERNAME']
            HAMMERHEAD_PASSWORD = config['HAMMERHEAD']['HAMMERHEAD_PASSWORD']
        except KeyError:
            print(f'Could not read {CONFIGFILE}. Please check again.')
            sys.exit(1)
    else:
        write_configfile(CONFIGFILE)

    # Get Hammerhead dashboard access token
    token = get_access_token(HAMMERHEAD_USERNAME, HAMMERHEAD_PASSWORD)

    # Get user ID from JWT token
    user = get_userid(token)

    # Get list of all workouts between these dates, default = only today
    workouts = get_workouts(WORKOUT_OLDEST_DATE, WORKOUT_NEWEST_DATE, INTERVALS_ICU_ID, INTERVALS_ICU_APIKEY)
    if workouts:
        for workout in workouts:
            workout_id = workout['id']
            workout_date = workout['date']
            workout_name = workout['name']
            # Remove invalid filename characters
            workout_name_clean =re.sub(r'[<>:/\|?*"]+',"", workout_name)
            filename = f"./zwo/{workout_date}_{workout_name_clean}.zwo"
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Get ZWO file for selected workout
            workout_zwo = get_workout(workout_id, INTERVALS_ICU_ID, INTERVALS_ICU_APIKEY)

            with open(filename,'w') as f:
                f.write(workout_zwo)
                f.close()

            files = {'file': open(filename, 'rb')}

            # Upload to Hammerhead
            upload_workout(user, token, files)
            print(f'Synced {workout_date}: {workout_name}')

    else:
        print('No workouts found.')
        sys.exit(0)

    
if __name__ == "__main__":
    main()
