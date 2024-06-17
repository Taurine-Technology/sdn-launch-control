import json
import subprocess
import time
import requests
import csv
import datetime
import os
import pytz
from dotenv import load_dotenv

load_dotenv()
bridge = os.getenv('BRIDGE')
openflow_version = os.getenv('OPENFLOW_VERSION', 'openflow13')
api_url = os.getenv('API_URL')
device_ip = os.getenv('DEVICE_IP')


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
    lines = output.strip().split('\n')[1:]  # Skip the first line which is a header
    stats = {}
    parts = len(lines)

    for i in range(0, parts, 3):
        # port name and rx packets
        temp1 = lines[i].strip()
        rx_stats = temp1.split(',')
        port_number = rx_stats[0].split(':')[0].split(' ')[-1]
        rx_pkts = rx_stats[0].split(':')[-1].split('=')[-1]
        rx_bytes = rx_stats[1].split('=')[-1]
        rx_drop = rx_stats[2].split('=')[-1]
        rx_errors = rx_stats[3].split('=')[-1]

        # port name and tx packets
        temp2 = lines[i + 1].strip()
        tx_stats = temp2.split(',')
        tx_pkts = tx_stats[0].split('=')[-1]
        tx_bytes = tx_stats[1].split('=')[-1]
        tx_drop = tx_stats[2].split('=')[-1]
        tx_errors = tx_stats[3].split('=')[-1]

        # duration
        temp3 = lines[i + 2].strip()
        duration_stats = temp3.split('=')
        duration = duration_stats[-1][:-1]

        stats[port_number] = {
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
            parts = line.split()  # Splitting by spaces
            port_info = parts[0].split('(')  # e.g., '9(eth2):'
            if len(port_info) > 1:
                port_num = port_info[0]  # '9'
                interface_name = port_info[1].rstrip('):')  # 'eth2'
                port_interface_map[port_num] = interface_name
    return port_interface_map


def get_interface_map(bridge):
    ret, output, _err = start_process(["sudo", "ovs-ofctl", "show", bridge, '-O', openflow_version])
    if ret == 0:
        print(output)
        return parse_port_interface_map(output)
    else:
        print(f"Error retrieving interface map: {_err}")
        return {}


if __name__ == "__main__":
    old_stats = {}
    port_interface_map = get_interface_map(bridge)
    while True:
        ret, out, _err = start_process(["sudo", "ovs-ofctl", "dump-ports", bridge, '-O', openflow_version])
        if ret == 0:
            print(out)
            current_stats = parse_ovs_statistics(out)
            if old_stats:
                differences = compute_differences(current_stats, old_stats)
                interface_differences = {}
                for port, stats in differences.items():
                    interface_name = port_interface_map.get(port, port)  # Fallback to port if no interface name found
                    interface_differences[interface_name] = stats

                log_data_to_csv('./logs.csv', interface_differences)
                data_to_send = {
                    'device_ip': device_ip,
                    'stats': interface_differences
                }
                code, response = send_data_to_api(api_url, data_to_send)
                print(data_to_send)
                print(f"API Response: {code} - {response}")
            old_stats = current_stats
        else:
            print(f"Error retrieving statistics: {_err}")
        time.sleep(1)
