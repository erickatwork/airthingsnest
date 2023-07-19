import sys
import logging
import yaml
import os
import json
import pytz
from datetime import datetime

from airthings import Airthings
from nest import Nest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
sh.setFormatter(formatter)
logger.addHandler(sh)

def convertCelsiustoFahrenheit(degree):
    if degree == None:
        return None
    f = (round((9 * degree) / 5 + 32, 2))
    logger.debug(f'Converting {degree} Celsius to {f} Fahrenheit')
    return f

def convertFahrenheittoCelsius(degree):
    if degree == None:
        return None
    c = (round((degree - 32) * 5 / 9, 2))
    logger.debug(f'Converting {degree} Fahrenheit to {c} Celsius')
    return c

# Check if any air quality thresholds are breached and if so, enable fan
def check_air_quality(nest, nest_status, airthings_results, NEST_SECONDS_FAN_ON):
    if nest_status['fan_timer_active'] == "ON":
        logger.info('Fan is already on. Do nothing.')
        return False
    else:
        is_fan_enabled = False
        for device in airthings_results:
            if device['is_threshold_breached'] == True:
                nest.set_fan(NEST_SECONDS_FAN_ON)
                is_fan_enabled = True
                logger.info(f"Fan turned on for {NEST_SECONDS_FAN_ON} seconds because of {device['device_name']}.")
                break
        if is_fan_enabled == False:
            logger.info('No thresholds breached. Will not turn on fan.')
            return False
        else:
            return True

def main():
    logger.info('================================= Starting =================================')

    # Get client id and secret from config.json
    try:
        with open('config.yml', 'r') as f:
            config_variables = yaml.safe_load(f)
            NEST_SECONDS_FAN_ON = config_variables['nest_seconds_fan_on']
            RADON_THRESHOLD = config_variables['radon_threshold']
            PM25_THRESHOLD = config_variables['pm25_threshold']
            VOC_THRESHOLD = config_variables['voc_threshold']
            CO2_THRESHOLD = config_variables['co2_threshold']
            HUMIDITY_THRESHOLD = config_variables['humidity_threshold']

    except FileNotFoundError:
        logger.error('No config.json found')

    AIRTHINGS_CLIENT_ID = os.getenv('AIRTHINGS_CLIENT_ID')
    AIRTHINGS_CLIENT_SECRET = os.getenv('AIRTHINGS_CLIENT_SECRET')
    NEST_PROJECT_ID = os.getenv('NEST_PROJECT_ID')
    NEST_CLIENT_ID = os.getenv('NEST_CLIENT_ID')
    NEST_CLIENT_SECRET = os.getenv('NEST_CLIENT_SECRET')
    NEST_REDIRECT_URI = os.getenv('NEST_REDIRECT_URI')
    NEST_CODE = os.getenv('NEST_CODE')
    NEST_ACCESS_TOKEN = os.getenv('NEST_ACCESS_TOKEN')
    NEST_REFRESH_TOKEN = os.getenv('NEST_REFRESH_TOKEN')
    
    # Initialize oauth2 for Airthings API
    airthings = Airthings (
        client_id=AIRTHINGS_CLIENT_ID,
        client_secret=AIRTHINGS_CLIENT_SECRET
        )

    airthings.get_access_token()
    devices = airthings.get_devices()
    airthings.set_thresholds(RADON_THRESHOLD, PM25_THRESHOLD, VOC_THRESHOLD, CO2_THRESHOLD, HUMIDITY_THRESHOLD)

    # Get Airthings data
    airthings_results = []
    for device in devices['devices']:
        device_id = device['id']
        device_name = device['segment']['name'] # "Living room" or "Bedroom"
        latest_samples = airthings.get_latest_sample(device_id)
        latest_samples = latest_samples['data'] # Simplify structure
        latest_samples['ambient_temperature_fahrenheit'] = convertCelsiustoFahrenheit(latest_samples['temp'])
        latest_samples['ambient_temperature_celsius'] = latest_samples['temp'] # Rename for clearity
        del latest_samples['temp']
        is_threshold_breached = airthings.is_threshold_breached(device_name ,latest_samples)
        device_info = {'device_name': device_name, 'device_id': device_id, 'latest_samples': latest_samples, 'is_threshold_breached': is_threshold_breached}
        device_info = dict(sorted(device_info.items()))
        airthings_results.append(device_info)

    # Get Nest status
    nest = Nest(NEST_PROJECT_ID, NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_REDIRECT_URI, NEST_CODE, NEST_ACCESS_TOKEN, NEST_REFRESH_TOKEN)
    if NEST_CODE == None:  # only need this on the first run to get the URL to get the NEST_CODE to paste into config.json
        nest.get_code()

    nest.get_access_token()
    nest.get_device_name()
    nest_status = nest.get_thermostat_status()
    # Store fahrenheit values for easier debugging
    nest_status['cool_fahrenheit'] = convertCelsiustoFahrenheit(nest_status['cool_celsius'])
    nest_status['heat_fahrenheit'] = convertCelsiustoFahrenheit(nest_status['heat_celsius'])
    nest_status['ambient_temperature_fahrenheit'] = convertCelsiustoFahrenheit(nest_status['ambient_temperature_celsius'])
    nest_status = dict(sorted(nest_status.items()))

    # Log status of both devices
    logger.info(f'Airthings results:\n{ json.dumps(airthings_results, indent=4) }')
    logger.info(f'Nest status:\n{ json.dumps(nest_status, indent=4) }')

    # Check air quality and adjust fan if needed
    check_air_quality(nest, nest_status, airthings_results, NEST_SECONDS_FAN_ON)

    logger.info('================================= Complete =================================\n\n')


if __name__ == "__main__":
    main()