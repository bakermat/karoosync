## Overview

karoosync gets today's workout from [intervals.icu](https://intervals.icu) for usage on a Hammerhead Karoo bike computer.

## Getting Started
- Install this using `pip install karoosync`
- Get your [intervals.icu](https://intervals.icu) API key on your [account](https://intervals.icu/settings) page.
- Run `karoosync`, the first time it will create a `karoosync.cfg` config file in your current directory.
- Open `karoosync.cfg` and modify it as required:
    - The start & end dates that you want to get the activities for.
    - Your intervals.icu athlete id & API key.
    - Add your Hammerhead dashboard username & password.
- Make sure you've started your Hammerhead Karoo and you're already in the Workouts menu. If not, the workout will not show up.
- Run the app with `karoosync`.
- You'll see the workout show up on the Karoo, it won't show up on the Hammerhead dashboard: that's expected. 
- Do NOT click on Sync on either the Karoo or on the Hammerhead dashboard, as it will remove the workout again. If that happens, re-run the app while you're in the Workouts menu.

## Caveats
- Hammerhead officially only supports workouts created in TrainingPeaks or via the Xert app. Every time you click on 'Sync' on either the Karoo or on the Hammerhead dashboard, it will check for any changed workouts and remove workouts that weren't created on those platforms.
- Created workouts using this app will show up on the Karoo device, however they won't show up on the Hammerhead dashboard. Clicking Sync or refresh on the dashboard won't help, as it actually removes the workout because of the reason above.

## Disclaimer
This website is in no way affiliated with either Hammerhead or https://intervals.icu. It was developed for personal use and is not supported. I welcome pull requests if you want to contribute.
