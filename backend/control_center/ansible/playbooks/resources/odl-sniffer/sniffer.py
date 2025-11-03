# File: sniffer.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

import time
import threading
import subprocess
import re
import json
import requests
import logging
import os
from dotenv import load_dotenv
from scapy.all import sniff, Raw, IP, TCP, UDP, Ether, linehexdump
import ipaddress
import sys
from logging.handlers import RotatingFileHandler
import datetime

BATCH_INTERVAL = 5  # seconds
latest_flows = {}   # key: flow_key, value: flow_stat dict
batch_lock = threading.Lock()

# Load environment variables
load_dotenv()
BRIDGE = os.environ.get('BRIDGE')
API_BASE_URL = os.environ.get('API_BASE_URL')  # e.g., http://10.10.10.2:8000
ODL_CLASSIFY_ENDPOINT = "/api/v1/odl/classify/"  # Your specific ODL classification endpoint
INTERFACE = os.environ.get('INTERFACE')
PORT_TO_CLIENTS = os.environ.get('PORT_TO_CLIENTS')  # OpenFlow port number
PORT_TO_ROUTER = os.environ.get('PORT_TO_ROUTER')  # OpenFlow port number
NUM_BYTES = int(os.environ.get('NUM_BYTES'))
NUM_PACKETS = int(os.getenv('NUM_PACKETS'))
MODEL_NAME = os.getenv('MODEL_NAME')
ODL_SWITCH_NODE_ID = os.environ.get('ODL_SWITCH_NODE_ID')  # e.g., "openflow:172223708800235"
ODL_CONTROLLER_IP = os.environ.get('ODL_CONTROLLER_IP')  # e.g., "10.10.10.10"
GRACE_PERIOD = int(os.getenv('GRACE_PERIOD', 30))  # Default to 30 if not set

# Logger setup (defaults to minimal output; configurable via env)
logger = logging.getLogger(__name__)

LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()
ENABLE_CONSOLE_LOG = os.getenv('ENABLE_CONSOLE_LOG', '0').lower() in ('1', 'true', 'yes')
VERBOSE = os.getenv('VERBOSE', '0').lower() in ('1', 'true', 'yes')

level_map = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}
logger.setLevel(level_map.get(LOG_LEVEL, logging.WARNING))

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')

error_handler = RotatingFileHandler("error.log", maxBytes=2 * 1024 * 1024, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

# Only create a debug log file if explicitly configured via LOG_LEVEL
if logger.level <= logging.DEBUG:
    debug_handler = RotatingFileHandler("debug.log", maxBytes=2 * 1024 * 1024, backupCount=5)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)

if ENABLE_CONSOLE_LOG:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logger.level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Global dictionaries for flow state
flow_dict = {}  # Holds packet arrays per flow key: flow_key -> [packet_data_list]
flow_predicted = {}  # Whether a flow has been classified: flow_key -> bool
total_flow_len = {}  # Counting packets per flow key: flow_key -> int
flow_last_seen = {}  # Last seen timestamp for each flow: flow_key -> timestamp
flow_active_cookie_map = {}  # Mapping: flow_key -> cookie_value (int)

# flow_key -> {"c2s_match_str": "...", "s2c_match_str": "...", "cookie": 123}
flow_installation_details = {}

# --- Batching for classification API calls ---
# Instead of just a list of data, keep a list of (flow_key, data_to_send) tuples
classification_batch = []  # List of (flow_key, data_to_send)
batch_lock = threading.Lock()
BATCH_SEND_INTERVAL = 1  # seconds

def batch_sender():
    while True:
        time.sleep(BATCH_SEND_INTERVAL)
        with batch_lock:
            if classification_batch:
                try:
                    if not API_BASE_URL:
                        logger.error("API_BASE_URL is not set. Cannot send classification batch.")
                        classification_batch.clear()
                        continue
                    api_url = f"{API_BASE_URL.rstrip('/')}{ODL_CLASSIFY_ENDPOINT}"
                    headers = {'Content-Type': 'application/json'}
                    batch_to_send = classification_batch.copy()
                    flow_keys = [item[0] for item in batch_to_send]
                    data_list = [item[1] for item in batch_to_send]
                    if VERBOSE:
                        logger.debug(f"[BATCH SENDER] Sending batch of {len(data_list)} classifications to API: {api_url}")
                    response = requests.post(api_url, headers=headers, json=data_list, timeout=10)
                    response.raise_for_status()
                    logger.info(f"Sent batch of {len(data_list)} classifications to API. Response: {response.status_code}")
                    # Expect a list of results in the response
                    results = response.json()
                    if VERBOSE:
                        logger.debug(f"[BATCH SENDER] API response JSON: {results}")
                    if not isinstance(results, list):
                        logger.error("Batch API response is not a list!")
                    else:
                        for idx, result in enumerate(results):
                            flow_key = flow_keys[idx] if idx < len(flow_keys) else None
                            if flow_key is not None:
                                handle_classification_response(flow_key, result)
                except Exception as e:
                    logger.error(f"Batch send failed: {e}")
                classification_batch.clear()

# Start the batch sender thread
batch_thread = threading.Thread(target=batch_sender, daemon=True)
batch_thread.start()

def get_active_flow_matches_from_ovs():
    """
    Retrieve the match portion of active flows from OVS.
    Returns a set of strings, where each string is the "match" part of an OVS flow entry.
    e.g., {"tcp,in_port=2,dl_src=...", "udp,in_port=1,dl_dst=..."}
    """
    cmd = ["sudo", "ovs-ofctl", "dump-flows", BRIDGE, "-O", "Openflow13"]
    active_flow_match_parts = set()
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        flow_lines = result.stdout.splitlines()

        for line in flow_lines:
            line = line.strip()
            if not line or "actions=" not in line:
                continue

            # Extract the part before " actions="
            match_part = line.split(" actions=")[0].strip()

            # get match criteria, excluding cookie, duration, table, n_packets, n_bytes, priority
            # Example: "cookie=..., duration=..., table=0, n_packets=0, n_bytes=0, priority=60000,tcp,in_port=2,dl_src=..."
            # We want: "tcp,in_port=2,dl_src=..."
            match_criteria_only = re.sub(r'cookie=0x[0-9a-fA-F]+,?', '', match_part)
            match_criteria_only = re.sub(r'duration=[\d\.]+s,?', '', match_criteria_only)
            match_criteria_only = re.sub(r'table=\d+,?', '', match_criteria_only)
            match_criteria_only = re.sub(r'n_packets=\d+,?', '', match_criteria_only)
            match_criteria_only = re.sub(r'n_bytes=\d+,?', '', match_criteria_only)
            match_criteria_only = re.sub(r'priority=\d+,?', '', match_criteria_only)
            match_criteria_only = re.sub(r'idle_timeout=\d+,?', '', match_criteria_only)  # If idle_timeout is present
            match_criteria_only = re.sub(r'hard_timeout=\d+,?', '', match_criteria_only)  # If hard_timeout is present

            # Clean up leading/trailing commas and multiple commas
            match_criteria_only = match_criteria_only.strip(',')
            match_criteria_only = re.sub(r',,+', ',', match_criteria_only)

            if match_criteria_only:  # Ensure there's something left
                active_flow_match_parts.add(match_criteria_only)
                if VERBOSE:
                    logger.debug(match_criteria_only)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ovs-ofctl dump-flows: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error retrieving OVS flow matches: {e}", exc_info=True)
    logger.debug(f"Active flow match parts from OVS: {active_flow_match_parts}")
    return active_flow_match_parts

def get_active_cookies_from_ovs():
    """
    Retrieve the active flow cookies from OVS using ovs-ofctl.
    Returns a set of active cookie values (integers).
    """
    cmd = ["sudo", "ovs-ofctl", "dump-flows", BRIDGE, "-O", "Openflow13"]
    active_cookies = set()
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        flow_lines = result.stdout.splitlines()

        for line in flow_lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            # Example line: cookie=0x1b66, duration=11.519s, table=0, ...
            cookie_match = re.search(r'cookie=0x([0-9a-fA-F]+)', line)
            if cookie_match:
                try:
                    cookie_hex = cookie_match.group(1)
                    cookie_int = int(cookie_hex, 16)
                    active_cookies.add(cookie_int)
                except ValueError:
                    logger.error(f"Could not parse cookie from flow line: {line}")
            else:
                logger.debug(f"No cookie found in flow line: {line}") # Can be noisy
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ovs-ofctl dump-flows: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error retrieving OVS flow cookies: {e}", exc_info=True)
    logger.debug(f"Active cookies from OVS: {active_cookies}")
    return active_cookies


def is_private_ip(ip):
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        logger.warning(f"Invalid IP address for private check: {ip}")
        return False


def compute_flow_key(ip_src, ip_dst, protocol, sport, dport, mac):
    if is_private_ip(ip_src):
        # If src is private, it's likely our client. Key based on (client_ip, remote_ip, proto, client_port, remote_port, client_mac)
        return (ip_src, ip_dst, protocol, str(sport), str(dport), mac)
    else:
        # If dst is private, it's likely our client. Key based on (client_ip, remote_ip, proto, client_port, remote_port, client_mac)
        return (ip_dst, ip_src, protocol, str(dport), str(sport), mac)


def clear_expired_flows():
    """
    Periodically checks for flows whose cookies are no longer in OVS
    AND is not within the GRACE_PERIOD.
    Clears state for such expired flows.
    """
    logger.info("Expired flow cleanup thread started.")
    while True:
        try:
            active_ovs_match_strings = get_active_flow_matches_from_ovs()  # Get match strings
            current_time = time.time()
            expired_flow_keys = []

            for flow_key, details in list(flow_installation_details.items()):
                c2s_match_in_ovs = details.get("c2s_match") in active_ovs_match_strings
                s2c_match_in_ovs = details.get("s2c_match") in active_ovs_match_strings

                if not c2s_match_in_ovs and not s2c_match_in_ovs:  # If NEITHER direction is found
                    # Both directions of the flow are gone from OVS. Check grace period.
                    if flow_key in flow_last_seen and (current_time - flow_last_seen[flow_key]) >= GRACE_PERIOD:
                        logger.info(
                            f"Flow key {flow_key} (c2s_match='{details.get('c2s_match')}', s2c_match='{details.get('s2c_match')}') "
                            f"is expired. OVS flows gone and grace period passed. Clearing state.")
                        expired_flow_keys.append(flow_key)
                    elif flow_key not in flow_last_seen:
                        logger.warning(
                            f"Flow key {flow_key} has no last_seen timestamp but OVS flows are gone. Clearing state.")
                        expired_flow_keys.append(flow_key)
                    else:
                        logger.debug(
                            f"Flow key {flow_key} OVS flows (c2s:{c2s_match_in_ovs}, s2c:{s2c_match_in_ovs}) gone, "
                            f"but still within grace period.")
                else:
                    logger.debug(
                        f"Flow key {flow_key} still has active OVS flows (c2s found: {c2s_match_in_ovs}, s2c found: {s2c_match_in_ovs}). "
                        f"Cookie: {details.get('cookie')}")

            for key_to_delete in expired_flow_keys:
                flow_dict.pop(key_to_delete, None)
                flow_predicted.pop(key_to_delete, None)
                total_flow_len.pop(key_to_delete, None)
                flow_last_seen.pop(key_to_delete, None)
                flow_installation_details.pop(key_to_delete, None)  # Remove from new map
                logger.info(f"Cleared state for expired flow key: {key_to_delete}")

        except Exception as e:
            logger.error(f"Error in clear_expired_flows loop: {e}", exc_info=True)
        time.sleep(1)

# =====================
# Packet Processing
# =====================
def pkt_callback(pkt):
    global flow_dict, flow_predicted, total_flow_len, flow_last_seen
    key = None  # Initialize key
    decimal_data = []
    protocol = ""
    ip_src, ip_dst, sport, dport, mac = None, None, None, None, None  # Initialize

    try:
        if pkt.haslayer(IP):  # Process if it's an IP packet
            ip_src = pkt[IP].src
            ip_dst = pkt[IP].dst

            if pkt.haslayer(TCP):
                protocol = "TCP"
                sport = pkt[TCP].sport
                dport = pkt[TCP].dport
            elif pkt.haslayer(UDP):
                protocol = "UDP"
                sport = pkt[UDP].sport
                dport = pkt[UDP].dport
            else:  # Not TCP or UDP, ignore for flow classification based on ports
                return

            # Determine the MAC address of our local private IP device
            pkt_eth_src_mac = pkt[Ether].src
            pkt_eth_dst_mac = pkt[Ether].dst

            client_mac_for_key_and_api = None
            remote_mac_for_api = None

            if is_private_ip(ip_src):
                # Source IP is private, so it's our client.
                # The packet's source MAC is the client's MAC.
                # The packet's destination MAC is the remote MAC.
                client_mac_for_key_and_api = pkt_eth_src_mac
                remote_mac_for_api = pkt_eth_dst_mac
            elif is_private_ip(ip_dst):
                # Destination IP is private, so it's our client.
                # The packet's destination MAC is the client's MAC.
                # The packet's source MAC is the remote MAC.
                client_mac_for_key_and_api = pkt_eth_dst_mac
                remote_mac_for_api = pkt_eth_src_mac
            else:
                logger.debug(
                    f"Packet with no private IP identified as client: {ip_src} ({pkt_eth_src_mac}) -> {ip_dst} ({pkt_eth_dst_mac}). Skipping flow classification for this packet."
                )
                return

            # client_mac_for_key_and_api holds the MAC of the client device on our network.
            # And remote_mac_for_api holds the MAC of the device it's communicating with.
            key = compute_flow_key(ip_src, ip_dst, protocol, sport, dport, client_mac_for_key_and_api)
            total_flow_len[key] = total_flow_len.get(key, 0) + 1
            flow_last_seen[key] = time.time()

            if pkt.haslayer(Raw) and not pkt.haslayer('TLS'):  # Check for Raw payload
                # Only extract payload if it exists
                hex_data = linehexdump(pkt[IP].payload, onlyhex=1, dump=True).split(" ")
                # Filter out empty strings that can result from multiple spaces in hexdump
                hex_data = [h for h in hex_data if h]
                if hex_data:  # Proceed only if there's actual hex data
                    decimal_data = list(map(hex_to_dec, hex_data))
                    if len(decimal_data) >= NUM_BYTES:
                        decimal_data = decimal_data[:NUM_BYTES]
                    else:
                        decimal_data.extend([0] * (NUM_BYTES - len(decimal_data)))
                else:  # No payload data to process for this packet
                    decimal_data = [0] * NUM_BYTES  # Fill with zeros if no payload
            else:  # No Raw layer or it's TLS, fill with zeros
                decimal_data = [0] * NUM_BYTES

    except Exception as e:
        logger.error(f"Error processing packet: {e}", exc_info=True)
        return  # Stop processing this packet

    if key and decimal_data:  # Ensure key was formed and decimal_data exists
        if key not in flow_dict:
            flow_dict[key] = []
            flow_predicted[key] = False
            logger.debug(f"New flow started: {key}")

        if len(flow_dict[key]) < NUM_PACKETS:
            flow_dict[key].append(decimal_data)

        if len(flow_dict[key]) == NUM_PACKETS and not flow_predicted.get(key, False):
            flow_predicted[key] = True  # Mark as predicted to avoid re-sending
            logger.info(f"Collected {NUM_PACKETS} packets for flow key {key}. Triggering classification.")
            # Pass necessary details to classify function
            # Determine src (1 if ip_src is private, 0 otherwise)
            client_is_source_flag = 1 if is_private_ip(ip_src) else 0
            tcp_flag = 1 if protocol == "TCP" else 0

            # Create a new thread for the API call to avoid blocking sniffing
            api_thread = threading.Thread(target=classify_and_apply_policy, args=(
                key, ip_src, ip_dst, str(sport), str(dport),
                client_mac_for_key_and_api,  # This is the client's actual MAC
                remote_mac_for_api,  # This is the remote MAC address
                flow_dict[key], client_is_source_flag, tcp_flag
            ))
            api_thread.start()


def hex_to_dec(hex_str):
    try:
        return str(int(hex_str, 16))
    except ValueError:
        logger.warning(f"Could not convert hex to dec: '{hex_str}'")
        return "0"  # Return "0" for unparseable hex strings


def classify_and_apply_policy(flow_key, ip_src, ip_dst, src_port, dst_port, client_actual_mac, remote_actual_mac, packet_arr, src_flag, tcp_flag):
    global flow_installation_details # store cookie

    # Ensure environment variables for ODL are loaded and present
    if not ODL_SWITCH_NODE_ID or not ODL_CONTROLLER_IP:
        logger.error("ODL_SWITCH_NODE_ID or ODL_CONTROLLER_IP environment variable not set. Cannot classify.")
        return
    if not API_BASE_URL:
        logger.error("API_BASE_URL is not set. Cannot queue classification.")
        return
    # Prepare the data to send
    data_to_send = {
        "controller_ip": ODL_CONTROLLER_IP,
        "switch_id": ODL_SWITCH_NODE_ID,  # Use the ODL Node ID
        "src_ip": ip_src,
        "dst_ip": ip_dst,
        "src_port": src_port,
        "dst_port": dst_port,
        "src_mac": client_actual_mac,  # Client's MAC address
        "dst_mac": remote_actual_mac,  # MAC address of the other endpoint
        "payload": json.dumps(packet_arr),
        "src": src_flag,  # 1 if src_ip is client, 0 if dst_ip is client
        "tcp": tcp_flag,  # 1 for TCP, 0 for UDP
        "port_to_client": PORT_TO_CLIENTS,
        "port_to_router": PORT_TO_ROUTER,
        "model_name": MODEL_NAME
    }
    log_payload = data_to_send.copy()
    log_payload["payload"] = f"<{len(packet_arr)} packets omitted>"
    logger.debug(f"Queueing classification for batch send: {json.dumps(log_payload)}")

    # Instead of sending immediately, add (flow_key, data_to_send) to batch
    with batch_lock:
        classification_batch.append((flow_key, data_to_send))

# New function to handle the response for each flow

def handle_classification_response(flow_key, result):
    global flow_installation_details
    if VERBOSE:
        logger.debug(f"[HANDLE RESPONSE] Processing API response for flow key {flow_key}: {result}")
    logger.info(f"API Response for flow key {flow_key}: {result}")
    if result.get("status") == "success" and result.get("flow_results"):
        c2s_match_str_from_payload = None
        s2c_match_str_from_payload = None
        shared_cookie = None
        for flow_res in result["flow_results"]:
            if flow_res.get("status") == "success" and flow_res.get("payload_sent"):
                try:
                    sent_flow_data_list = flow_res["payload_sent"].get("flow-node-inventory:flow")
                    if not sent_flow_data_list:
                        continue
                    sent_flow_data = sent_flow_data_list[0]
                    if shared_cookie is None:  # Cookie is the same for c2s and s2c
                        shared_cookie = sent_flow_data.get("cookie")
                        if shared_cookie is not None:
                            shared_cookie = int(shared_cookie)
                    # Reconstruct a comparable OVS match string from ODL payload's match part
                    odl_match_obj = sent_flow_data.get("match", {})
                    ovs_style_match_str = convert_odl_match_to_ovs_str(odl_match_obj)
                    flow_id_from_payload = sent_flow_data.get("id", "")
                    if "c2s" in flow_id_from_payload:
                        c2s_match_str_from_payload = ovs_style_match_str
                    elif "s2c" in flow_id_from_payload:
                        s2c_match_str_from_payload = ovs_style_match_str
                except Exception as e:
                    logger.error(f"Error processing flow result for cookie/match extraction: {e}")
        if c2s_match_str_from_payload and s2c_match_str_from_payload and shared_cookie is not None:
            flow_installation_details[flow_key] = {
                "c2s_match": c2s_match_str_from_payload,
                "s2c_match": s2c_match_str_from_payload,
                "cookie": shared_cookie  # Store the category cookie for reference
            }
            logger.debug(
                f"Stored installation details for flow key {flow_key}: c2s_match='{c2s_match_str_from_payload}', s2c_match='{s2c_match_str_from_payload}', cookie={shared_cookie}")
        else:
            logger.warning(
                f"Could not store full installation details for flow_key {flow_key}. c2s: {c2s_match_str_from_payload}, s2c: {s2c_match_str_from_payload}")
    # else: could log errors or handle other statuses

def convert_odl_match_to_ovs_str(odl_match_obj):
    """
    Converts an ODL match object (from the flow payload) into a string
    that aims to be comparable with the match part of ovs-ofctl dump-flows output.
    This is complex due to ordering and exact formatting.
    Returns a sorted, comma-separated string of key=value pairs.
    """
    if not odl_match_obj:
        return ""

    ovs_match_parts = []

    # Protocol (tcp, udp) - derived from ip-match.ip-protocol
    ip_match = odl_match_obj.get("ip-match", {})
    ip_protocol = ip_match.get("ip-protocol")
    if ip_protocol == 6:
        ovs_match_parts.append("tcp")
    elif ip_protocol == 17:
        ovs_match_parts.append("udp")
    # Add other protocols if needed (icmp, etc.)

    # In-port
    if "in-port" in odl_match_obj:
        ovs_match_parts.append(f"in_port={odl_match_obj['in-port']}")  # OVS uses in_port

    # Ethernet Match
    eth_match = odl_match_obj.get("ethernet-match", {})
    if eth_match:
        # dl_type (EtherType) - OVS shows it as hex, e.g., dl_type=0x0800
        # ODL has {"ethernet-type": {"type": 2048}}
        eth_type_obj = eth_match.get("ethernet-type")
        if eth_type_obj and "type" in eth_type_obj:
            ovs_match_parts.append(f"dl_type=0x{eth_type_obj['type']:04x}")

        eth_src_obj = eth_match.get("ethernet-source")
        if eth_src_obj and "address" in eth_src_obj:
            ovs_match_parts.append(f"dl_src={eth_src_obj['address'].lower()}")

        eth_dst_obj = eth_match.get("ethernet-destination")
        if eth_dst_obj and "address" in eth_dst_obj:
            ovs_match_parts.append(f"dl_dst={eth_dst_obj['address'].lower()}")

    # L4 Ports
    if "tcp-source-port" in odl_match_obj:
        ovs_match_parts.append(f"tp_src={odl_match_obj['tcp-source-port']}")
    if "tcp-destination-port" in odl_match_obj:
        ovs_match_parts.append(f"tp_dst={odl_match_obj['tcp-destination-port']}")
    if "udp-source-port" in odl_match_obj:
        ovs_match_parts.append(f"tp_src={odl_match_obj['udp-source-port']}")
    if "udp-destination-port" in odl_match_obj:
        ovs_match_parts.append(f"tp_dst={odl_match_obj['udp-destination-port']}")

    # IMPORTANT: Sort the parts to ensure consistent string for comparison
    ovs_match_parts.sort()
    return ",".join(ovs_match_parts)

# --- Main Execution ---
def main():
    logger.info("Initializing SDN Launch Control Sniffer for OpenDaylight...")

    # Start the flow expiration checker thread
    clear_thread = threading.Thread(target=clear_expired_flows, daemon=True)
    clear_thread.start()

    logger.info(f"Starting packet sniffing on interface: {INTERFACE}")
    try:
        # Consider adding a BPF filter to sniff only relevant traffic if INTERFACE is busy
        # E.g., filter="ip and (tcp or udp)"
        sniff(iface=INTERFACE, prn=pkt_callback, store=0)
    except PermissionError:
        logger.error(f"Permission denied to sniff on interface {INTERFACE}. Try running as root or with sudo.")
    except OSError as e:  # Catches "No such device" or similar
        logger.error(f"OS error sniffing on interface {INTERFACE}: {e}. Check if interface exists and is up.")
    except Exception as e:
        logger.error(f"Critical error starting packet sniffing: {e}", exc_info=True)


if __name__ == '__main__':
    main()

