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

# Load environment variables and set up logger as before
load_dotenv()
BRIDGE = os.environ.get('BRIDGE')
API_BASE_URL = os.environ.get('API_BASE_URL')
INTERFACE = os.environ.get('INTERFACE')
PORT_TO_CLIENTS = os.environ.get('PORT_TO_CLIENTS')
PORT_TO_ROUTER = os.environ.get('PORT_TO_ROUTER')
NUM_BYTES = int(os.environ.get('NUM_BYTES'))
NUM_PACKETS = int(os.getenv('NUM_PACKETS'))
MODEL_NAME = os.getenv('MODEL_NAME')
LAN_IP_ADDRESS = os.environ.get('LAN_IP_ADDRESS')

# Set a grace period (in seconds) to wait before clearing flow state
GRACE_PERIOD = 30


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Debug log: Rotating file handler (max 2MB, 5 backups)
debug_handler = RotatingFileHandler("debug.log", maxBytes=2*1024*1024, backupCount=5)
debug_handler.setLevel(logging.DEBUG)
debug_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
debug_handler.setFormatter(debug_formatter)

# Error log: Rotating file handler for errors only (max 2MB, 5 backups)
error_handler = RotatingFileHandler("error.log", maxBytes=2*1024*1024, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)

# Console handler to print log messages to stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(debug_formatter)

# Add the handlers to the logger
logger.addHandler(debug_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)

# Global dictionaries for flow state
flow_dict = {}         # Holds packet arrays per flow key
flow_predicted = {}    # Whether a flow has been classified
total_flow_len = {}    # Counting packets per flow key
flow_cookie_map = {}   # Mapping: flow key -> list of flow IDs (as decimal strings)

flow_selector_map = {}  # Mapping: flow key -> selectors
flow_last_seen = {}  # Last seen timestamp for each flow



# ========= ONOS Selector Handling =========
def get_active_flows_from_ovs():
    """
    Retrieve the active flows from OVS using ovs-ofctl.
    return list of active flows {cookie,in port,IP_PROTO,macaddress,port,direction}
    """
    cmd = ["sudo", "ovs-ofctl", "dump-flows", BRIDGE, "-O", "openflow13"]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        flows = result.stdout.splitlines()
        active_flows = []

        for line in flows:
            # get details
            arr = line.split(',')
            if len(arr)  < 2:
                continue
            meter_item = arr[-2]
            # this is a flow we care about
            if 'meter' in meter_item:
                try:
                    cookie = arr[0].split('=')[1]
                    port = meter_item.split('=')[1].split(' ')[0]
                    mac = arr[-3].split('=')[1]
                    dir = arr[-3].split('=')[-1]

                    direction = 'src' if 'src' in dir else 'dst'
                    in_port = arr[-4].split('=')[1]
                    protocol = arr[-5].lower()

                    # Determine IP protocol number (TCP = 6, UDP = 17)
                    ip_protocol = 6 if protocol == 'tcp' else 17

                    flow = {
                        'cookie': cookie,
                        'port': port,
                        'IP_PROTO': ip_protocol,
                        'mac_address': mac,
                        'IN_PORT': in_port,
                        'direction': direction,
                    }

                    # Map flows together: Match source with destination flow based on IP_PROTO, MAC, and PORT
                    if direction == 'src':
                        flow['ETH_SRC'] = mac
                        if protocol == 'udp':
                            flow['UDP_SRC'] = port
                        else:
                            flow['TCP_SRC'] = port
                    else:
                        flow['ETH_DST'] = mac
                        if protocol == 'udp':
                            flow['UDP_DST'] = port
                        else:
                            flow['TCP_DST'] = port


                    active_flows.append(flow)
                except IndexError as e:
                    logger.error(f"Error parsing OVS flow line: {line} - {e}")

        # logger.debug(f'active flows from ovs: {active_flows}')
        return active_flows
    except Exception as e:
        logger.error("Error retrieving OVS flows: %s", e)
        return []

def is_private_ip(ip):
    """
    Check if an IP address is private.
    :param ip: the IP address
    :return: true if it is private else false
    """
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False

def compute_flow_key(ip_src, ip_dst, protocol, sport, dport, mac):
    """
    Returns a consistent key for a flow.
    If ip_src is private, use:
       key = ip_src + ip_dst + protocol + sport + dport + mac
    Otherwise, use:
       key = ip_dst + ip_src + protocol + dport + sport + mac
    """
    if is_private_ip(ip_src):
        return ip_src + ip_dst + protocol + str(sport) + str(dport) + mac
    else:
        return ip_dst + ip_src + protocol + str(dport) + str(sport) + mac


def clear_expired_flows():
    """
    Poll the OVS flow table and clear keys that have no matching cookies
    AND have not been updated within the grace period.
    """
    while True:

        active_flows = get_active_flows_from_ovs()
        current_time = time.time()
        expired_keys = []

        for key, selectors in list(flow_selector_map.items()):

            # Only consider flows that haven't been updated within the grace period
            if key in flow_last_seen and (current_time - flow_last_seen[key]) < GRACE_PERIOD:
                continue
            src_sel = selectors[0]
            dst_sel = selectors[1]

            # Check if the flow exists in active flows
            flow_exists = False

            for flow in active_flows:
                if flow['direction'] == 'src':
                    match_criteria = src_sel
                else:
                    match_criteria = dst_sel
                match_criteria.pop('ETH_TYPE', None)


                if all(match_criteria.get(k) == flow.get(k) for k in match_criteria):
                    flow_exists = True
                    logger.debug(f"found a match for flow: {key}")
                    break
            if not flow_exists:
                logger.debug(f"Removing expired flow: {key}")
                expired_keys.append(key)
        for key in expired_keys:
            flow_selector_map.pop(key, None)
            flow_dict.pop(key, None)
            flow_predicted.pop(key, None)
            total_flow_len.pop(key, None)
            flow_last_seen.pop(key, None)
        time.sleep(5)

def extract_selectors(api_response):
    try:
        # Ensure the API response is a dict
        if not isinstance(api_response, dict):
            logger.error("API response is not a dict; skipping selectors extraction")
            return None, None

        flow_results = api_response.get("flow_results")
        # Check that flow_results exists and is a dict (not an empty list)
        if not flow_results or not isinstance(flow_results, dict):
            logger.debug("No valid flow_results found; skipping selectors extraction")
            return None, None

        flow_rule_src = flow_results.get("flow_rule_src", {}).get("flows", [])
        flow_rule_dst = flow_results.get("flow_rule_dst", {}).get("flows", [])

        if flow_rule_src and flow_rule_dst:
            src_criteria = {
                c["type"]: c.get("mac") or c.get("port") or c.get("protocol") or c.get("tcpPort") or c.get("udpPort")
                for c in flow_rule_src[0].get("selector", {}).get("criteria", [])
            }
            dst_criteria = {
                c["type"]: c.get("mac") or c.get("port") or c.get("protocol") or c.get("tcpPort") or c.get("udpPort")
                for c in flow_rule_dst[0].get("selector", {}).get("criteria", [])
            }
            return src_criteria, dst_criteria
        else:
            logger.error("Flow rules missing in ONOS response")
            return None, None
    except Exception as e:
        logger.error("Error parsing API response JSON: %s", e)
        return None, None

# =====================
# Packet Processing
# =====================
def pkt_callback(pkt):
    global flow_dict, flow_predicted, total_flow_len, flow_last_seen
    key = ""
    decimal_data = []
    protocol = ""
    try:
        if pkt.haslayer(IP) and pkt.haslayer(Raw) and not pkt.haslayer('TLS'):
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
            else:
                return
            if is_private_ip(ip_src):
                mac = pkt[Ether].src
            else:
                mac = pkt[Ether].dst

            key = compute_flow_key(ip_src, ip_dst, protocol, sport, dport, mac)
            total_flow_len[key] = total_flow_len.get(key, 0) + 1
            # Record the last seen timestamp for this key
            flow_last_seen[key] = time.time()

            hex_data = linehexdump(pkt[IP].payload, onlyhex=1, dump=True).split(" ")
            decimal_data = list(map(hex_to_dec, hex_data))
            if len(decimal_data) >= NUM_BYTES:
                decimal_data = decimal_data[:NUM_BYTES]
            else:
                decimal_data.extend([0]*(NUM_BYTES - len(decimal_data)))
        elif pkt.haslayer(IP):
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
            else:
                return
            if is_private_ip(ip_src):
                mac = pkt[Ether].src
            else:
                mac = pkt[Ether].dst
            key = compute_flow_key(ip_src, ip_dst, protocol, sport, dport, mac)
            total_flow_len[key] = total_flow_len.get(key, 0) + 1
            flow_last_seen[key] = time.time()
    except Exception as e:
        logger.error("Error reading packet: %s", e)

    if decimal_data:
        if key in flow_dict:
            pkts = flow_dict[key]
            if len(pkts) < NUM_PACKETS:
                flow_dict[key].append(decimal_data)
            if len(pkts) == NUM_PACKETS and not flow_predicted[key]:
                flow_predicted[key] = True

                # logger.debug("Triggering API call for key %s with packet info: %s", key, json.dumps(pkt_info, indent=2))
                # logger.debug("Collected %d packets for key %s", len(pkts), key)
                classify(key, ip_src, ip_dst, str(sport), str(dport), mac, flow_dict[key],
                         (1 if is_private_ip(ip_src) else 0), (1 if protocol=="TCP" else 0))
                return
        else:
            flow_dict[key] = [decimal_data]
            flow_predicted[key] = False

def hex_to_dec(hex_data):
    return str(int(hex_data, 16))

# =====================
# Classification Function
# =====================
def classify(flow_key, ip_src, ip_dst, src_port, dst_port, src_mac, packet_arr, src, tcp):
    headers = {'Content-Type': 'application/json'}
    protected_url = f"{API_BASE_URL}/api/v1/classify/"
    data = {
        "model_name": MODEL_NAME,
        "src_ip": ip_src,
        "dst_ip": ip_dst,
        "src_port": src_port,
        "dst_port": dst_port,
        "src_mac": src_mac,
        "dst_mac": src_mac,
        "payload": json.dumps(packet_arr),
        "src": src,
        "tcp": tcp,
        "lan_ip_address": LAN_IP_ADDRESS,
        "port_to_client": PORT_TO_CLIENTS,
        "port_to_router": PORT_TO_ROUTER
    }
    json_data = json.dumps(data)
    temp_data = json.loads(json_data)
    temp_data["payload"] = "omitted"
    # logger.debug("API Request Data: %s", json.dumps(temp_data))

    def send_request():
        while True:
            try:
                response = requests.post(protected_url, headers=headers, data=json_data, timeout=5)
                return response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                logger.error("API call failed, retrying in 10 seconds")
                time.sleep(10)
            except requests.exceptions.RequestException as e:
                logger.error("API call error: %s", e)
                return None
    response = send_request()
    if response is None:
        logger.error("Failed to get a response after multiple attempts.")
        return
    try:
        result = response.json()

        print(result)
        src_selectors, dst_selectors = extract_selectors(result)

        if src_selectors and dst_selectors:
            flow_selector_map[flow_key] = [src_selectors, dst_selectors]
            # logger.debug(f"Flow {flow_key} registered with selectors: {src_selectors} and {dst_selectors}")

    except Exception as e:
        logger.error("Error parsing API response: %s", e)

    # logger.debug("Classification successful, response: %s", response.text)

# =====================
# Main Function
# =====================
def main():
    # Start a background thread to clear expired flows
    clear_thread = threading.Thread(target=clear_expired_flows, daemon=True)
    clear_thread.start()
    try:
        sniff(iface=INTERFACE, prn=pkt_callback, store=0)
    except Exception as e:
        logger.error("Error starting packet sniffing: %s", e)

if __name__ == '__main__':
    main()
