# File: classification.py
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

import json


class Classification:
    def __init__(self, src_ip, dst_ip, src_port, dst_port, src_mac, payload, src, outer_ipv4, client_port, tcp,
                 inbound_port, outbound_port, switch_id):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.src_mac = src_mac
        self.payload = payload
        self.src = src
        self.outer_ipv4 = outer_ipv4
        self.client_port = client_port
        self.tcp = tcp
        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.switch_id = switch_id


def create_classification_from_json(json_data):
    src_ip = json_data.get("src_ip")
    dst_ip = json_data.get("dst_ip")
    src_port = json_data.get("src_port")
    dst_port = json_data.get("dst_port")
    src_mac = json_data.get("src_mac")
    payload = json_data.get("payload")
    src = json_data.get("src")
    tcp = json_data.get("tcp")  # 1 is tcp and 0 is udp
    inbound_port = json_data.get("inbound_port")
    outbound_port = json_data.get("outbound_port")
    switch_id = json_data.get("switch_id")
    payload = json.loads(payload)
    # print(payload)
    if src_ip and dst_ip and src_port and dst_port and src_mac and src == 1:  # the client is sending the packet
        return Classification(src_ip, dst_ip, src_port, dst_port, src_mac, payload, src, outer_ipv4=dst_ip,
                              client_port=src_port, tcp=tcp, inbound_port=inbound_port, outbound_port=outbound_port,
                              switch_id=switch_id)
    elif src_ip and dst_ip and src_port and dst_port and src_mac and src == 0:
        return Classification(src_ip, dst_ip, src_port, dst_port, src_mac, payload, src, outer_ipv4=src_ip,
                              client_port=dst_port, tcp=tcp, inbound_port=inbound_port, outbound_port=outbound_port,
                              switch_id=switch_id)
    else:
        print(src_ip, dst_ip, src_port, dst_port, src_mac, src, tcp, switch_id, inbound_port, outbound_port)
        raise ValueError("Invalid parameters")

