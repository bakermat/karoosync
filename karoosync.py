import json
import requests
import jwt
from base64 import b64encode
from bs4 import BeautifulSoup
from datetime import datetime


###############################################################################################
# Change the credentials below to match your intervals.icu & Hammerhead dashboard credentials #
###############################################################################################
INTERVALS_ICU_ID = "i00000"
INTERVALS_ICU_APIKEY = "00000000000000000000"
HAMMERHEAD_USERNAME = "your_email_address"
HAMMERHEAD_PASSWORD = "your_password"


###########################################################################
# Don't change anything below this line unless you know what you're doing #
###########################################################################
# By default this app will fetch today's workout and sync it with the Hammerhead Dashboard.
# No point in trying to get additional workouts, as they get auto-deleted whenever the Karoo syncs (manual or auto).
WORKOUT_OLDEST_DATE = datetime.today().strftime('%Y-%m-%d')
WORKOUT_NEWEST_DATE = datetime.today().strftime('%Y-%m-%d')


def get_access_token(username, password):
    url = "https://dashboard.hammerhead.io/v1/auth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "grant_type": "password",
        "username": username,
        "password": password
    }
    response = requests.post(url, headers=headers, data=payload).json()
    access_token = response['access_token']
    return access_token


def get_userid(token):
    jwt_data = jwt.decode(token, algorithms="HS256", options={"verify_signature": False})
    user = jwt_data['sub']
    return user


def get_workouts(oldest, newest):
    url = f'https://intervals.icu/api/v1/athlete/{INTERVALS_ICU_ID}/events?oldest={oldest}&newest={newest}'

    token = b64encode(f'API_KEY:{INTERVALS_ICU_APIKEY}'.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'text/plain'
    }
    workouts = call_api(url, "GET", headers).json()
    for workout in workouts:
        if workout['type'] == "Ride" and workout['start_date_local'][0:10] == WORKOUT_OLDEST_DATE:
            workout_id = workout['id']
            date = workout['start_date_local'][0:10]
            json_workout = {'id': workout_id, 'date': date}

    return json_workout


def get_workout(workout_id):
    url = f'https://intervals.icu/api/v1/athlete/{INTERVALS_ICU_ID}/events/{workout_id}/downloadzwo'

    token = b64encode(f'API_KEY:{INTERVALS_ICU_APIKEY}'.encode()).decode()
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
    except Exception as err:
        raise(err)
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
            "secondaryTarget": {
                "type": "cadence",
                "value": cadence
            },
            "type": "step"
        }
        list_structure.append(structure)

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
    # Get Hammerhead dashboard access token
    token = get_access_token(HAMMERHEAD_USERNAME, HAMMERHEAD_PASSWORD)

    # Get user ID from JWT token
    user = get_userid(token)

    # Get list of all workouts between these dates, default = only today
    workout = get_workouts(WORKOUT_OLDEST_DATE, WORKOUT_NEWEST_DATE)
    workout_id = workout['id']
    workout_date = workout['date']

    # Get ZWO file for selected workout
    workout_zwo = get_workout(workout_id)

    # Convert ZWO file to Hammerhead JSON
    workout_hammerhead = convert_zwo(workout_zwo, workout_date)

    # Upload to Hammerhead
    response = upload_workout(user, token, workout_hammerhead)
    print(f'Successfully created workout {response.text.strip()}\nYou should see this workout on your Karoo device now if you are in the Workouts menu. Re-run this script if you are not, as a manual or automatic SYNC will delete this workout again.')


if __name__ == "__main__":
    main()
