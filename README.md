# Automation for Airthings + Nest Thermostat

Use Airthings measurements to control Nest Thermostat to ensure healthy air and comfortable temperatures.

This is mostly just the Airthings and Nest libraries to get you started. You'll need to impliemnt your own logic to control fans or HVAC.

### Fan Thresholds
- Radon >= 2.7 pCi/L / >= 100 Bq/m3
- PM2.5 >= 10 ug/m3
- VOC >= 250 ppb
- CO2 >= 800 ppm
- Humidity 25% >= x >= 60%

## Adjust AC if...
1. AC is on, but the measured temp from Airthings does not match Nest

# Requirements

### Hardware
- Airthings View Plus. I've only tested it with the View, but it should work with other devices
- Nest Thermostat

### Setup
- Smart Device Management (SDM) API - There are several steps to get API access. I followed this [article](https://geoffhudik.com/tech/2023/03/04/trying-google-nest-api-with-postman-and-python/). Note: to get API access, you must pay a one-time $5 fee to Google.
- Airthings API - You'll need an Airthings account to generate an [API key](https://developer.airthings.com/api-docs#tag/Devices).
- Python/Pipenv
- Optional: update values in `config.yaml`
- If running locally, setup environment variables. If running via GitHub Actions, setup repo secrets. 
    ```
    AIRTHINGS_CLIENT_ID
    AIRTHINGS_CLIENT_SECRET
    NEST_PROJECT_ID
    NEST_CLIENT_ID
    NEST_CLIENT_SECRET
    NEST_REDIRECT_URI
    NEST_CODE
    NEST_ACCESS_TOKEN
    NEST_REFRESH_TOKEN
    ```
- If running for the first name you'll need to run `nest.get_code()` and add the output to the env variable `NEST_CODE`.