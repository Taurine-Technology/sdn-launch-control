import psutil
import json
import requests
import time
import logging
import os

# Set up logging
logging.basicConfig(filename='system_stats.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


def get_system_stats():
    stats = {
        "ip_address": os.getenv("DEVICE_IP", "127.0.0.1"),
        "cpu": psutil.cpu_percent(interval=None),  # Non-blocking call
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }
    return json.dumps(stats)


def send_stats_to_server(stats):
    url = os.getenv("API_URL", "http://localhost:8000/api/v1/post_device_stats/")
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{url}/api/v1/post_device_stats/', data=stats, headers=headers)
    logging.info(f"Posted stats to server: {stats}")
    return response.status_code


if __name__ == "__main__":
    while True:
        stats = get_system_stats()
        logging.info(f"Collected stats: {stats}")
        rsp = send_stats_to_server(stats)
        print(rsp)
        time.sleep(1)
