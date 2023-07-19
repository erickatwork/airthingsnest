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

class Airthings:    
    token_url = "https://accounts-api.airthings.com/v1/token"
    ext_url = "https://ext-api.airthings.com/v1/"
    expires_in = ""

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, access_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.set_thresholds()
    
    # Set thresholds for air quality
    def set_thresholds(self, radon_threshold=100, pm25_threshold=10, voc_threshold=250, co2_threshold=800, humidity_threshold=60):
        self.radon_threshold = radon_threshold
        self.pm25_threshold = pm25_threshold
        self.voc_threshold = voc_threshold
        self.co2_threshold = co2_threshold
        self.humidity_threshold = humidity_threshold

    def get_access_token(self):        
        token_url=self.token_url
        client_id=self.client_id
        client_secret=self.client_secret
        token_req_payload = {
            "grant_type": "client_credentials",
            "scope": "read:device:current_values",
        }

        # Request Access Token from auth server
        try:
            token_response = requests.post(
                token_url,
                data=token_req_payload,
                allow_redirects=False,
                auth=(client_id, client_secret),
            )
        except requests.HTTPError as e:
            logger.error(e)

        if token_response and token_response.status_code == 200:
            token_response = token_response.json()
            self.access_token = token_response['access_token']
            self.expires_in = token_response['expires_in']
        else:
            logger.error('{"Error":"Token credentials incorrect. Check your secret or client id"}')

    def get_endpoint(self, endpoint, query_string=None):
        query_string = query_string.decode('utf-8') if query_string else ''
        try:
            api_headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"{self.ext_url}{endpoint}{f'?{query_string}'}"
            response = requests.get(url=url, headers=api_headers)
        except requests.HTTPError as e:
            logger.error(e)

        if response and response.status_code == 200:
            logger.debug(f"Response: {response.json()}")
            response = response.json()
            return response
        else:
            logger.error(f"Error: {response.json()}")
            sys.exit(1)

    def get_devices(self, device_id=None, query_string=None):
        if device_id:
            return self.get_endpoint(f"devices/{device_id}", query_string)
        else:
            return self.get_endpoint("devices", query_string)

    def get_latest_sample(self, device_id, query_string=None):
        return self.get_endpoint(f"devices/{device_id}/latest-samples", query_string)

    def get_threshold_breaches(self, device_id, query_string=None):
        return self.get_endpoint(f"devices/{device_id}/threshold-breaches", query_string)

    def get_latest_segment(self, device_id, query_string=None):
        return self.get_endpoint(f"devices/{device_id}/latest-segment", query_string)

    def get_device_sample(self, device_id, query_string=None):
        return self.get_endpoint(f"devices/{device_id}/samples", query_string)

    def get_locations(self, query_string=None):
        return self.get_endpoint("locations", query_string)

    def get_segments(self, query_string=None):
        return self.get_endpoint("segments", query_string)

    def get_samples_from_segment(self, segment, query_string=None):
        return self.get_endpoint(f"segments/{segment}/samples", query_string)

    def is_threshold_breached(self, device_name=None, latest_samples=None):

        threshold_breached = False
        if latest_samples['radonShortTermAvg'] > self.radon_threshold:
            logger.info(f'{device_name} Radon threshold breached: {latest_samples["radonShortTermAvg"]}')
            threshold_breached = True
        if latest_samples['pm25'] > self.pm25_threshold:
            logger.info(f'{device_name} PM2.5 threshold breached: {latest_samples["pm25"]}')
            threshold_breached = True
        if latest_samples['voc'] > self.voc_threshold:
            logger.info(f'{device_name} VOC threshold breached: {latest_samples["voc"]}')
            threshold_breached = True
        if latest_samples['co2'] > self.co2_threshold:
            logger.info(f'{device_name} CO2 threshold breached: {latest_samples["co2"]}')
            threshold_breached = True
        if latest_samples['humidity'] > self.humidity_threshold:
            logger.info(f'{device_name} Humidity threshold breached: {latest_samples["humidity"]}')
            threshold_breached = True
        return threshold_breached

