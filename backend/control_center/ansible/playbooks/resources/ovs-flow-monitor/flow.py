import json
import subprocess
import sys
import time
import csv
import datetime
import os
import re
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import requests

load_dotenv()
# Configuration
BRIDGE = os.getenv('BRIDGE', 'odl-br')
OPENFLOW_VERSION = os.getenv('OPENFLOW_VERSION', 'Openflow13')
CSV_FILE = os.getenv('CSV_OUTPUT_FILE', './odl_flow_stats.csv')
# POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '5'))
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')
STATS_ENDPOINT = os.getenv('STATS_API_ENDPOINT', '/api/v1/network/log-flow-stats/')
# BACKEND_API_AUTH_TOKEN = os.getenv('BACKEND_API_AUTH_TOKEN')

POLL_INTERVAL = 10 

# Set up a logger that only logs errors to a rotating file (max 2MB)
logger = logging.getLogger("flow")
logger.setLevel(logging.ERROR)
handler = RotatingFileHandler("flow_errors.log", maxBytes=2 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_flows_from_ovs(bridge, of_version):
    """Retrieve flow statistics from the specified OVS bridge."""
    try:
        cmd = ["sudo", "ovs-ofctl", "dump-flows", bridge, "-O", of_version]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error retrieving flows: {e.stderr}")
        return ""

def parse_flow_line_for_stats(line):
    """
    Parse an OVS flow dump line to extract stats and cookie.
    Returns a dictionary of relevant fields or None if not a relevant flow.
    """
    flow_data = {}
    if "cookie=" not in line or "actions=" not in line:
        return None

    # Extract cookie first (as integer)
    cookie_match = re.search(r'cookie=0x([0-9a-fA-F]+)', line)
    if cookie_match:
        try:
            flow_data['cookie'] = int(cookie_match.group(1), 16)
        except ValueError:
            logger.warning(f"Could not parse cookie from line: {line}")
            return None # Cannot proceed without a valid cookie
    else:
        return None # No cookie, likely not one of our flows
    # Extract actions to check for meter
    actions_match = re.search(r'actions=(.*)', line)
    actions_str = actions_match.group(1) if actions_match else ""

    meter_match = re.search(r'meter:(\d+)', actions_str)
    flow_data['meter_id'] = int(meter_match.group(1)) if meter_match else 0  # Default to 0 if no meter

    # only want to log stats for flows that HAVE a meter action:
    if not meter_match:
        return None
    # Extract other stats fields
    # Duration: duration=123.456s
    duration_match = re.search(r'duration=([\d\.]+)s', line)
    flow_data['duration_sec'] = float(duration_match.group(1)) if duration_match else 0.0

    # Packets: n_packets=123
    packets_match = re.search(r'n_packets=(\d+)', line)
    flow_data['packet_count'] = int(packets_match.group(1)) if packets_match else 0

    # Bytes: n_bytes=12345
    bytes_match = re.search(r'n_bytes=(\d+)', line)
    flow_data['byte_count'] = int(bytes_match.group(1)) if bytes_match else 0

    # Priority: priority=30000
    priority_match = re.search(r'priority=(\d+)', line)
    flow_data['priority'] = int(priority_match.group(1)) if priority_match else 0

    # Attempt to get protocol, MAC, port for context (can be less reliable from dump-flows)
    # These are more for context in the CSV/API call, primary grouping is by cookie.
    protocol = ""
    if "tcp" in line.lower():
        protocol = "tcp"
    elif "udp" in line.lower():
        protocol = "udp"
    elif "icmp" in line.lower():
        protocol = "icmp"
    elif "arp" in line.lower():
        protocol = "arp"
    flow_data['protocol'] = protocol

    dl_src_match = re.search(r'dl_src=([0-9a-fA-F:]+)', line)
    dl_dst_match = re.search(r'dl_dst=([0-9a-fA-F:]+)', line)
    flow_data['mac_address'] = dl_src_match.group(1) if dl_src_match else (
        dl_dst_match.group(1) if dl_dst_match else "")

    tp_src_match = re.search(r'tp_src=(\d+)', line)
    tp_dst_match = re.search(r'tp_dst=(\d+)', line)
    port_val = 0
    if tp_src_match:
        port_val = int(tp_src_match.group(1))
    elif tp_dst_match:
        port_val = int(tp_dst_match.group(1))
    flow_data['port'] = port_val

    return flow_data

def prepare_stats_for_api(flow_stats_dict, timestamp_iso):
    """
    Prepares the record for the API, mapping fields as expected by the backend.
    The backend `create_flow_stat_entry` expects:
    timestamp, meter, duration, packets, bytes, priority, mac_address, protocol, port, classification (cookie here)
    """
    return {
        "timestamp": timestamp_iso,
        "meter": flow_stats_dict.get('meter_id', 0), # Meter ID applied to the flow
        "duration": f"{flow_stats_dict.get('duration_sec', 0.0):.3f}s", # Format duration string
        "packets": flow_stats_dict.get('packet_count', 0),
        "bytes": flow_stats_dict.get('byte_count', 0),
        "priority": flow_stats_dict.get('priority', 0),
        "mac_address": flow_stats_dict.get('mac_address', ""),
        "protocol": flow_stats_dict.get('protocol', ""),
        "port": flow_stats_dict.get('port', 0),
        "classification": str(flow_stats_dict.get('cookie', 'unknown_cookie')) # Using COOKIE as classification identifier
    }

def log_to_csv(file_path, records_for_api):
    file_exists = os.path.isfile(file_path)
    # Use fieldnames expected by your API/CSV format
    fieldnames = ['timestamp', 'meter', 'duration', 'packets', 'bytes', 'priority',
                  'mac_address', 'protocol', 'port', 'classification']
    try:
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists or os.path.getsize(file_path) == 0: # Check if file is empty too
                writer.writeheader()
            for rec in records_for_api:
                writer.writerow(rec)
        logger.info(f"Successfully wrote {len(records_for_api)} records to {file_path}")
    except IOError as e:
        logger.error(f"IOError writing to CSV {file_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error writing to CSV {file_path}: {e}", exc_info=True)


def send_stats_to_api(records_for_api):
    if not records_for_api:
        logger.info("No flow stats to send to API.")
        return True, None  # Nothing to send is a form of success

    api_full_url = f"{API_URL.rstrip('/')}" + f"{STATS_ENDPOINT.rstrip('/')}" + "/"
    headers = {'Content-Type': 'application/json'}
    # if BACKEND_API_AUTH_TOKEN:
    #     headers['Authorization'] = f"Token {BACKEND_API_AUTH_TOKEN}"

    logger.info(f"Attempting to send {len(records_for_api)} flow stat records to API: {api_full_url}")
    try:
        response = requests.post(api_full_url, headers=headers, json=records_for_api, timeout=15)

        if 200 <= response.status_code < 300:
            logger.info(f"Batch API call successful: {response.status_code} - {response.text[:200]}")
            return True, response
        else:
            logger.error(f"API call failed: {response.status_code} - {response.text}")
            return False, response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling API for batch: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error in send_stats_to_api: {e}", exc_info=True)
        return False, None


def main():
    print(f"Flow stats monitor started. Bridge: {BRIDGE}, Poll Interval: {POLL_INTERVAL}s")
    logger.info(f"Flow stats monitor started. Bridge: {BRIDGE}, Poll Interval: {POLL_INTERVAL}s")
    if not BRIDGE:
        logger.error("BRIDGE environment variable not set. Exiting.")
        sys.exit(1)

    while True:
        ovs_output = get_flows_from_ovs(BRIDGE, OPENFLOW_VERSION)
        if ovs_output:
            flow_lines = ovs_output.strip().splitlines()
            parsed_records_for_api = []
            latest_flows = {}
            current_timestamp_iso = datetime.datetime.utcnow().isoformat() + "Z"  # Add Z for UTC

            for line in flow_lines:
                if 'cookie=' in line and 'actions=' in line:  # Basic filter for valid flow lines
                    flow_stats = parse_flow_line_for_stats(line)
                    if flow_stats:
                        actions_raw = ""
                        actions_match = re.search(r'actions=(.*)', line)
                        if actions_match:
                            actions_raw = actions_match.group(1)

                        if 'controller' not in actions_raw.lower():  # Skip controller flows
                            flow_key = (
                                flow_stats.get('cookie'),
                                flow_stats.get('priority'),
                                flow_stats.get('mac_address'),
                                flow_stats.get('protocol'),
                                flow_stats.get('port')
                            )
                            # Always keep the latest reading (overwrites previous in this interval)
                            latest_flows[flow_key] = flow_stats

            parsed_records_for_api = [
                prepare_stats_for_api(flow_stats, current_timestamp_iso)
                for flow_stats in latest_flows.values()
            ]                

            if parsed_records_for_api:
                log_to_csv(CSV_FILE, parsed_records_for_api)

                # Retry sending to API until successful
                api_sent_successfully = False
                api_response = None
                while not api_sent_successfully:
                    api_sent_successfully, api_response = send_stats_to_api(parsed_records_for_api)
                    if api_sent_successfully:
                        print(f"Submitted batch with {len(parsed_records_for_api)} flows. API response: "
                              f"{api_response.status_code if api_response else 'No response'} - "
                              f"{api_response.text[:200] if api_response else ''}")
                    else:
                        logger.warning(f"API send failed. Retrying in {POLL_INTERVAL * 2} seconds...")
                        time.sleep(POLL_INTERVAL * 2)  # Wait longer on API failure before retry
            else:
                logger.info(f"[{current_timestamp_iso}] No relevant flows found for stats logging.")
        else:
            logger.info("No flow data retrieved from OVS.")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()