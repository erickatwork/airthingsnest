import os
import sys
import json
import logging
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
sh.setFormatter(formatter)
logger.addHandler(sh)

class Nest:

    oauth_url = 'https://www.googleapis.com/oauth2/v4/token/'
    api_url = 'https://smartdevicemanagement.googleapis.com/v1/'
    project_id = ""
    client_id = ""
    client_secret = ""
    redirect_uri = ""
    code = ""
    access_token = ""
    refresh_token = ""
    device_name = ""

    def __init__(self, project_id=None, client_id=None, client_secret=None, redirect_uri=None, code=None, access_token=None, refresh_token=None):
        self.project_id = project_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.code = code
        self.access_token = access_token
        self.refresh_token = refresh_token

    # Use to get "code" then paste it into the config. We dont need to do this again.
    def get_code(self):
        logger.debug('Getting code')
        url = 'https://nestservices.google.com/partnerconnections/'+self.project_id+'/auth?redirect_uri='+self.redirect_uri+'&access_type=offline&prompt=consent&client_id='+self.client_id+'&response_type=code&scope=https://www.googleapis.com/auth/sdm.service'
        print(f'Go to this URL to log in: {url}')
        print('Use the code from the URL between ?code=.....&scope=')

    def get_access_token(self):
        logger.debug('Getting access token')
        params = (
            ('client_id', self.client_id),
            ('client_secret', self.client_secret),
            ('code', self.code),
            ('grant_type', 'authorization_code'),
            ('redirect_uri', self.redirect_uri),
        )
        response = requests.post(self.oauth_url, params=params)

        response_json = response.json()
        if response.status_code == 200:
            self.access_token = response_json['token_type'] + ' ' + str(response_json['access_token'])
            self.refresh_token = response_json['refresh_token']
        else:
            self.get_refresh_token()

    def get_refresh_token(self):
        logger.debug('Getting refresh token')
        params = (
            ('client_id', self.client_id),
            ('client_secret', self.client_secret),
            ('refresh_token', self.refresh_token),
            ('grant_type', 'refresh_token'),
        )

        response = requests.post(self.oauth_url, params=params)
        response_json = response.json()
        access_token = response_json['token_type'] + ' ' + response_json['access_token']
        self.access_token = access_token


    def get_endpoint(self, endpoint, body = {}):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.access_token,
        }

        url = f"{self.api_url}{endpoint}"
        logger.debug(f'Getting endpoint {url}\n')
        if body:
            try:
                response = requests.post(url=url, headers=headers, data=json.dumps(body))
            except requests.HTTPError as e:
                logger.error(e)
        else:
            try:
                response = requests.get(url=url, headers=headers)
            except requests.HTTPError as e:
                logger.error(e)
        logger.debug(f'Response: {response.json(), response.status_code}')
        if response and response.status_code == 200:
            response = response.json()
            return response
        else:
            logger.error(f"Error: {response.json()}")
            sys.exit(1)


    # Get the first device which is the thermostat
    def get_device_name(self):
        logger.debug(f'Getting device name')
        endpoint = f'enterprises/{self.project_id}/devices'
        response_json = self.get_endpoint(endpoint)
        self.device_name = response_json['devices'][0]['name']

    def get_thermostat_status(self):
        logger.debug(f'Getting thermostat status')
        endpoint = f'{self.device_name}'
        response_json = self.get_endpoint(endpoint)
        thermostat_status = {
            'status': response_json['traits']['sdm.devices.traits.ThermostatHvac']['status'], # Will show "OFF" if not actively cooling or heating
            'humidity': response_json['traits']['sdm.devices.traits.Humidity']['ambientHumidityPercent'],
            'ambient_temperature_celsius': response_json['traits']['sdm.devices.traits.Temperature']['ambientTemperatureCelsius'],
            'mode': response_json['traits']['sdm.devices.traits.ThermostatMode']['mode'],
        }
        # These values aren't always present
        thermostat_status['heat_celsius'] = response_json['traits']['sdm.devices.traits.ThermostatTemperatureSetpoint'].get('heatCelsius', None)
        thermostat_status['cool_celsius'] = response_json['traits']['sdm.devices.traits.ThermostatTemperatureSetpoint'].get('coolCelsius', None)
        thermostat_status['fan_timer_active'] = response_json['traits']['sdm.devices.traits.Fan'].get('timerMode', None)
        thermostat_status['fan_timer_duration'] = response_json['traits']['sdm.devices.traits.Fan'].get('timerTimeout', None)
        logger.debug(f'Thermostat status: {thermostat_status}')
        return thermostat_status
    

    # Duration in seconds
    def set_fan(self, duration=900):
        logger.debug(f'Setting fan timer to {duration} seconds')
        endpoint = f'{self.device_name}:executeCommand'
        body = {
            "command" : "sdm.devices.commands.Fan.SetTimer",
            "params" : {
                "timerMode" : "ON",
                "duration" : f'{duration}s'
            }
        }
        response_json = self.get_endpoint(endpoint, body)
        if response_json:
            return True
        else:
            return False

    # Available modes : ['HEAT', 'COOL', 'HEATCOOL', 'OFF']
    def set_mode(self, mode='OFF'):
        mode = mode.upper()
        logger.debug(f'Setting mode {mode}')
        endpoint = f'{self.device_name}:executeCommand'
        body = {
            "command" : "sdm.devices.commands.ThermostatMode.SetMode",
            "params" : {
                "mode" : mode
            }
        }
        response_json = self.get_endpoint(endpoint, body)
        if response_json:
            return True
        else:
            return False

    # Available modes : ['MANUAL_ECO', 'OFF']
    def set_eco_mode(self, mode='MANUAL_ECO'):
        logger.debug(f'Setting eco mode {mode}')
        endpoint = f'{self.device_name}:executeCommand'
        body = {
            "command" : "sdm.devices.commands.ThermostatEco.SetMode",
            "params" : {
                "mode" : "MANUAL_ECO"
            }
        }
        response_json = self.get_endpoint(endpoint, body)
        if response_json:
            return True
        else:
            return False

    # Available modes : ['Heat', 'Cool']
    def set_temp(self, mode: str, tempC: float):
        self.set_mode(mode)
        logger.debug(f'Setting temp {tempC}C')
        endpoint = f'{self.device_name}:executeCommand'
        body = {
            "command": f"sdm.devices.commands.ThermostatTemperatureSetpoint.Set{mode}",
            "params": {
                f"{mode}Celsius": tempC
            }
        }
        response_json = self.get_endpoint(endpoint, body)
        if response_json:
            return True
        else:
            return False
    
    def set_temp_range(self, heat_tempC: float, cool_tempC: float):
        self.set_mode('HEATCOOL')
        logger.debug(f'Setting temp range. Heat: {heat_tempC}C, Cool: {cool_tempC}C')
        endpoint = f'{self.device_name}:executeCommand'
        body = {
            "command": f"sdm.devices.commands.ThermostatTemperatureSetpoint.SetRange",
            "params": {
                "heatCelsius": heat_tempC,
                "coolCelsius": cool_tempC
            }
        }
        response_json = self.get_endpoint(endpoint, body)
        if response_json:
            return True
        else:
            return False