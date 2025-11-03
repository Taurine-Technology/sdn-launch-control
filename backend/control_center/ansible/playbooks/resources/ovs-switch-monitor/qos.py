import json
import subprocess
import time
import requests
import csv
import datetime
import os
import pytz
from dotenv import load_dotenv
import re
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()
bridge = os.getenv('BRIDGE')
openflow_version = os.getenv('OPENFLOW_VERSION', 'openflow13')
api_url = os.getenv('API_URL')
device_ip = os.getenv('DEVICE_IP')

# Minimal-by-default logging with env controls
LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()
ENABLE_CONSOLE_LOG = os.getenv('ENABLE_CONSOLE_LOG', '0').lower() in ('1', 'true', 'yes')
VERBOSE = os.getenv('VERBOSE', '0').lower() in ('1', 'true', 'yes')

logger = logging.getLogger("qos")
level_map = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}
logger.setLevel(level_map.get(LOG_LEVEL, logging.WARNING))

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler = RotatingFileHandler("qos_errors.log", maxBytes=2 * 1024 * 1024, backupCount=3)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

if logger.level <= logging.DEBUG:
    debug_handler = RotatingFileHandler("qos_debug.log", maxBytes=2 * 1024 * 1024, backupCount=2)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)

if ENABLE_CONSOLE_LOG:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logger.level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def log_data_to_csv(file_path, data, buffer_size=10):
    sa_timezone = pytz.timezone('Africa/Johannesburg')
    file_exists = os.path.isfile(file_path)

    # Open the file with buffering, here 'buffer_size' is the number of lines to buffer
    with open(file_path, 'a', newline='', buffering=1) as csvfile:
        fieldnames = ['timestamp', 'port', 'rx_pkts_diff', 'tx_pkts_diff', 'rx_bytes_diff', 'tx_bytes_diff',
                      'duration_diff']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()  # Write header only once

        for port, stats in data.items():
            # Get the current time in UTC and then convert it to South Africa time zone
            now_utc = datetime.datetime.now(pytz.utc)
            now_south_africa = now_utc.astimezone(sa_timezone)

            stats['timestamp'] = now_south_africa.isoformat()
            stats['port'] = port
            writer.writerow(stats)

        # Manual flush based on buffer size
        if csvfile.tell() % buffer_size == 0:
            csvfile.flush()


def start_process(args):
    try:
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        return p.returncode, output.decode('utf-8'), err.decode('utf-8')
    except OSError as e:
        return -1, None, str(e)


def send_data_to_api(url, data):
    headers = {'Content-Type': 'application/json'}
    rsp = requests.post(url, data=json.dumps(data), headers=headers)
    return rsp.status_code, rsp.text


def parse_ovs_statistics(output):
    lines = output.strip().split('\n')[1:]  # Skip header
    stats = {}
    # Process every three lines (rx, tx, duration)
    for i in range(0, len(lines), 3):
        # Use regex to extract the port name after "port" and before the colon
        m = re.search(r'port\s+(\S+):', lines[i])
        if m:
            port_id = m.group(1)
        else:
            port_id = "unknown"

        # Now extract the stats values (using your original split logic)
        rx_stats = lines[i].strip().split(',')
        rx_pkts = rx_stats[0].split(':')[-1].split('=')[-1]
        rx_bytes = rx_stats[1].split('=')[-1]
        rx_drop = rx_stats[2].split('=')[-1]
        rx_errors = rx_stats[3].split('=')[-1]

        temp2 = lines[i + 1].strip()
        tx_stats = temp2.split(',')
        tx_pkts = tx_stats[0].split('=')[-1]
        tx_bytes = tx_stats[1].split('=')[-1]
        tx_drop = tx_stats[2].split('=')[-1]
        tx_errors = tx_stats[3].split('=')[-1]

        temp3 = lines[i + 2].strip()
        duration_stats = temp3.split('=')
        duration = duration_stats[-1][:-1]

        stats[port_id] = {
            'rx_pkts': int(rx_pkts),
            'rx_bytes': int(rx_bytes),
            'rx_drop': int(rx_drop),
            'rx_errors': int(rx_errors),
            'tx_pkts': int(tx_pkts),
            'tx_bytes': int(tx_bytes),
            'tx_drop': int(tx_drop),
            'tx_errors': int(tx_errors),
            'duration': float(duration)
        }
    return stats


def compute_differences(new_stats, old_stats):
    diff = {}
    for port in new_stats:
        if port in old_stats:
            diff[port] = {
                'rx_pkts_diff': new_stats[port]['rx_pkts'] - old_stats[port]['rx_pkts'],
                'tx_pkts_diff': new_stats[port]['tx_pkts'] - old_stats[port]['tx_pkts'],
                'rx_bytes_diff': new_stats[port]['rx_bytes'] - old_stats[port]['rx_bytes'],
                'tx_bytes_diff': new_stats[port]['tx_bytes'] - old_stats[port]['tx_bytes'],
                'duration_diff': new_stats[port]['duration'] - old_stats[port]['duration']
            }
    return diff


def parse_port_interface_map(output):
    port_interface_map = {}
    lines = output.splitlines()
    for line in lines:
        if 'addr' in line:
            parts = line.split()  # e.g., ["1(eth1):", "addr:9c:a2:f4:fc:24:eb"]
            port_info = parts[0].split('(')  # For "1(eth1):" → ["1", "eth1):"]
            if len(port_info) > 1:
                port_num = port_info[0]
                interface_name = port_info[1].rstrip('):')
                # Add both mappings: numeric port and interface name map to the interface name
                port_interface_map[port_num] = interface_name
                port_interface_map[interface_name] = interface_name
            else:
                key = parts[0].rstrip(':')
                port_interface_map[key] = key
    return port_interface_map


def get_interface_map(bridge):
    ret, output, _err = start_process(["sudo", "ovs-ofctl", "show", bridge, '-O', openflow_version])
    if ret == 0:
        if VERBOSE:
            logger.debug(output)
        return parse_port_interface_map(output)
    else:
        logger.error(f"Error retrieving interface map: {_err}")
        return {}


if __name__ == "__main__":
    old_stats = {}
    port_interface_map = get_interface_map(bridge)
    while True:
        ret, out, _err = start_process(["sudo", "ovs-ofctl", "dump-ports", bridge, '-O', openflow_version])
        if ret == 0:
            if VERBOSE:
                logger.debug(out)
            current_stats = parse_ovs_statistics(out)
            if old_stats:
                differences = compute_differences(current_stats, old_stats)
                interface_differences = {}
                for port, stats in differences.items():
                    interface_name = port_interface_map.get(port, port)  # Fallback to port if no interface name found
                    interface_differences[interface_name] = stats

                # log_data_to_csv('./logs.csv', interface_differences)
                data_to_send = {
                    'device_ip': device_ip,
                    'stats': interface_differences
                }
                code, response = send_data_to_api(f'{api_url}/api/v1/post_openflow_metrics/', data_to_send)
                if VERBOSE:
                    logger.debug(f"API Response: {code} - {response}")
            old_stats = current_stats
        else:
            logger.error(f"Error retrieving statistics: {_err}")
        time.sleep(1)
