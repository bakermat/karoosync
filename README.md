## Overview

karoosync gets today's workout from [intervals.icu](https://intervals.icu) for usage on a Hammerhead Karoo bike computer.

## Getting Started
- Install this using `pip install karoosync`
- Get your [intervals.icu](https://intervals.icu) API key on your [account](https://intervals.icu/settings) page.
- Run `karoosync`, the first time it will create a `karoosync.cfg` config file in your current directory.
- Open `karoosync.cfg` and modify it as required:
    - The start & end dates that you want to get the activities for, can be the same date if you only want one day.
    - Your intervals.icu athlete id & API key.
    - Add your Hammerhead dashboard username & password.
- Run the app with `karoosync`.
- You'll see the workout show up in the dashboard under workouts and on your Karoo.

## Caveat
If you run the app multiple times for the same date, you will see duplicates in the Hammerhead dashboard that might have to be removed manually. Bandwidth permitting I'll try to improve that workflow in a future version.

## Disclaimer
This website is in no way affiliated with either Hammerhead or https://intervals.icu. It was developed for personal use and is not supported. I welcome pull requests if you want to contribute.
