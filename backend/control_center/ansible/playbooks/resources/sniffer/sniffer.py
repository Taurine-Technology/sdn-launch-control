import time
from scapy.all import *
from requests.auth import HTTPBasicAuth
import requests
import json
import os
import logging
from dotenv import load_dotenv

class CustomLogger(logging.Logger):
    SUCCESS_LEVEL = 25

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        logging.addLevelName(self.SUCCESS_LEVEL, "SUCCESS")

    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(self.SUCCESS_LEVEL):
            self._log(self.SUCCESS_LEVEL, message, args, **kwargs)


# Setup logging to use the custom logger
logging.setLoggerClass(CustomLogger)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Lowest level for logger

# File handler for success messages
success_handler = logging.FileHandler("./success.log")
success_handler.setLevel(CustomLogger.SUCCESS_LEVEL)
success_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# File handler for general logging
general_handler = logging.FileHandler("./debug.log")
general_handler.setLevel(logging.DEBUG)  # Should handle DEBUG and above
general_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Console handler for general output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # INFO and above to the console
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add handlers to the logger
logger.addHandler(success_handler)
logger.addHandler(general_handler)
logger.addHandler(console_handler)

# Read the environment variables
load_dotenv()
SWITCH_ID = os.environ.get('SWITCH_ID')
API_BASE_URL = os.environ.get('API_BASE_URL')
INTERFACE = os.environ.get('INTERFACE')
PORT_TO_CLIENTS = os.environ.get('PORT_TO_CLIENTS')
PORT_TO_ROUTER = os.environ.get('PORT_TO_ROUTER')
NUM_BYTES = int(os.environ.get('NUM_BYTES'))
NUM_PACKETS = int(os.getenv('NUM_PACKETS'))
MODEL_NAME = os.getenv('MODEL_NAME')
LAN_IP_ADDRESS = os.getenv('LAN_IP_ADDRESS')

total_flow_len = {}
flow_dict = {}
flow_predicted = {}
pkt_arr = []
predictions = 0
count = 0
white_list_ips = []


def main():

    try:
        sniff(iface=INTERFACE, prn=pkt_callback, store=0)
    except Exception as e:
        logger.info(f"An error occurred starting sniff at line 67: {e}")


def pkt_callback(pkt):
    global count
    global flow_dict
    global flow_predicted
    count += 1
    # print(count)

    # print("Processing packet")
    # pkt.show()  # debug statement
    num_bytes = NUM_BYTES
    decimal_data = []
    protocol = ""
    key = ""
    src_mac = ''
    # print("called")
    start_time = time.time()
    try:
        if pkt.haslayer(IP) and pkt.haslayer(Raw) and not pkt.haslayer('TLS'):  # if there is a payload
            # print('reading packet data')

            # print("payload")
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
            src_mac = pkt[Ether].src
            src = 1  # if src is 1 then the source is a local client
            if ip_src[:3] == "10.":
                key = ip_src + ip_dst + protocol + str(sport) + str(dport) + str(src_mac)
            else:
                src_mac = pkt[Ether].dst
                src = 0
                key = ip_dst + ip_src + protocol + str(dport) + str(sport) + str(src_mac)
            if key in flow_predicted:
                if flow_predicted[key]:
                    return
            hex_data = linehexdump(
                pkt[IP].payload, onlyhex=1, dump=True).split(" ")
            decimal_data = list(map(hex_to_dec, hex_data))
            # fix length of payload
            if len(decimal_data) >= num_bytes:
                decimal_data = decimal_data[:num_bytes]
            elif len(decimal_data) < num_bytes:
                for i in range(len(decimal_data), num_bytes):
                    decimal_data.append(0)
            # for i in range(20):
            #     decimal_data[i] = 0  # mask first 20 bytes
            if key in total_flow_len:
                total_flow_len[key] = total_flow_len[key] + 1
            else:
                total_flow_len[key] = 1
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
            src_mac = pkt[Ether].src
            src = 1
            if ip_src[:3] == "10.":
                key = ip_src + ip_dst + protocol + str(sport) + str(dport) + str(src_mac)
            else:
                src_mac = pkt[Ether].dst
                src = 0
                key = ip_dst + ip_src + protocol + str(dport) + str(sport) + str(src_mac)
            if key in total_flow_len:
                total_flow_len[key] = total_flow_len[key] + 1
            else:
                total_flow_len[key] = 1
    except Exception as e:
        print(e)
        print("Error reading data with scapy")
        logger.info(f"Error reading data with scapy at line 160: {e}")
    if decimal_data:  # if there is an IPv4 payload to analyse
        # print("decimal data")
        # np_arr = np.array(decimal_data)
        if key in flow_dict:
            pkts = flow_dict[key]
            # print('previous time is', time_previous)
            if len(pkts) < NUM_PACKETS:
                flow_dict[key].append(decimal_data)
            if len(pkts) == NUM_PACKETS and not flow_predicted[key]:
                flow_predicted[key] = True
                if protocol == "TCP":
                    if src == 1:
                        # if source is client then inbound port is port to client
                        classify(ip_dst, ip_src, str(sport), str(dport), str(src_mac), pkts, src, 1,
                                 lan_ip=LAN_IP_ADDRESS, inbound_port=PORT_TO_CLIENTS, outbound_port=PORT_TO_ROUTER)
                    else:
                        classify(ip_dst, ip_src, str(sport), str(dport), str(src_mac), pkts, src, 1,
                                 lan_ip=LAN_IP_ADDRESS, inbound_port=PORT_TO_ROUTER, outbound_port=PORT_TO_CLIENTS)
                else:
                    if src == 1:
                        classify(ip_dst, ip_src, str(sport), str(dport), str(src_mac), pkts, src, 0,
                                 lan_ip=LAN_IP_ADDRESS, inbound_port=PORT_TO_CLIENTS, outbound_port=PORT_TO_ROUTER)
                    else:
                        classify(ip_dst, ip_src, str(sport), str(dport), str(src_mac), pkts, src, 0,
                                 lan_ip=LAN_IP_ADDRESS, inbound_port=PORT_TO_ROUTER, outbound_port=PORT_TO_CLIENTS)
                # print(pkts)
                # make_flow_adjustment(prediction, src_mac, 'None')
                # print('final total time is')
                return
        else:
            flow_dict[key] = [decimal_data]
            flow_predicted[key] = False
            # print('trying to add transformation time')
        # pkt_arr.append(decimal_data)


def classify(src_ip, dst_ip, src_port, dst_port, src_mac, packet_arr, src, tcp, lan_ip, inbound_port,
             outbound_port):
    headers = {
        'Content-Type': 'application/json'
    }

    protected_url = f"{API_BASE_URL}/classify/"

    data = {
        "model_name": MODEL_NAME,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "src_mac": src_mac,
        "payload": json.dumps(packet_arr),
        "src": src,
        "tcp": tcp,
        "lan_ip_address": lan_ip,
        "inbound_port": inbound_port,
        "outbound_port": outbound_port
    }

    # Convert the dictionary to a JSON string
    json_data = json.dumps(data)

    def send_request():
        indefinite_retry = True
        while indefinite_retry:
            try:
                protected_response = requests.post(protected_url, headers=headers, data=json_data, timeout=5)
                return protected_response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                retry_interval = 10
                print("API call failed, retrying in {} seconds".format(retry_interval))
                logger.info("API call failed at line 233... connection or timeout error")
                time.sleep(retry_interval)
            except requests.exceptions.RequestException as e:
                print('Error occurred:', e)
                logger.info(f"API call failed at line 237: {e}")

        return None  # return None after max_retry attempts

    response = send_request()

    if response is None:
        print("Failed to get a response after multiple attempts.")
        logger.info("Failed to get a response after multiple attempts at line 245")
        return

    if response is not None:
        # Print the response from the protected endpoint
        print(response.text)
        logger.success("Classification successful - %s", response.text)
    else:
        print("Failed to get a response after refreshing the token.")
        logging.info("Failed classification or bad response: %s", response)


def hex_to_dec(hex_data):
    return str(int(hex_data, base=16))


if __name__ == '__main__':
    main()
