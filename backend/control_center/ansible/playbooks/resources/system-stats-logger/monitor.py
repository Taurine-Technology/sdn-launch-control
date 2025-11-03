import psutil
import json
import requests
import time
import logging
import os

# Minimal-by-default logging with env controls
LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()
VERBOSE = os.getenv('VERBOSE', '0').lower() in ('1', 'true', 'yes')

level_map = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}

logging.basicConfig(
    filename='system_stats.log',
    level=level_map.get(LOG_LEVEL, logging.WARNING),
    format='%(asctime)s:%(levelname)s:%(message)s'
)


def get_system_stats():
    stats = {
        "ip_address": os.getenv("DEVICE_IP", "127.0.0.1"),
        "cpu": psutil.cpu_percent(interval=None),  # Non-blocking call
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }
    return json.dumps(stats)


def send_stats_to_server(stats):
    url = os.getenv("API_URL", "http://localhost:8000")
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{url}/api/v1/post_device_stats/', data=stats, headers=headers)
    logging.info(f"Posted stats to server: {stats}")
    return response.status_code


if __name__ == "__main__":
    while True:
        stats = get_system_stats()
        if VERBOSE:
            logging.debug(f"Collected stats: {stats}")
        rsp = send_stats_to_server(stats)
        if VERBOSE:
            logging.debug(f"Post status: {rsp}")
        time.sleep(1)
