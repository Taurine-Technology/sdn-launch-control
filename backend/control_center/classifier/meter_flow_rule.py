# File: meter_flow_rule.py
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


import requests
from requests.auth import HTTPBasicAuth
from utils.meter import convert_onos_meter_api_id_to_internal_id


class MeterFlowRule(object):

    def __init__(self, proto, client_port,
                 inbound_port_src, outbound_port_src,
                 inbound_port_dst, outbound_port_dst,
                 category, src_mac, dst_mac, controller_ip, meter_id, switch_id):
        # CHANGED HERE: Use separate ports for src and dst flows
        self.protocol = proto
        self.client_port = client_port
        self.inbound_port_src = inbound_port_src
        self.outbound_port_src = outbound_port_src
        self.inbound_port_dst = inbound_port_dst
        self.outbound_port_dst = outbound_port_dst
        self.category = category
        self.src_mac = src_mac
        self.controller_ip = controller_ip
        self.meter_id = meter_id
        self.switch_id = switch_id
        self.priority = 55000
        self.timeout = 360
        self.is_permanent = 'false'
        self.dst_mac = dst_mac
        # get device ID
    def _build_flow_rule(self, protocol, direction, numeric_meter_id):
        """
        Constructs a flow rule dictionary for the given protocol ('tcp' or 'udp')
        and direction ('src' or 'dst'). Uses instance variables for port, MAC, etc.
        """
        rule = {
            "flows": [
                {
                    "priority": self.priority,
                    "timeout": self.timeout,
                    "isPermanent": self.is_permanent,
                    "deviceId": self.switch_id,
                    "treatment": {
                    "instructions": [
                            {"type": "OUTPUT", "port": self._get_output_port(direction)},
                            {"type": "METER", "meterId": numeric_meter_id}
                        ]
                    },
                    "selector": {
                        "criteria": []  # Will be populated below
                    }
                }
            ]
        }

        criteria = rule["flows"][0]["selector"]["criteria"]
        # Common criteria: Ethernet Type (IPv4)
        criteria.append({"type": "ETH_TYPE", "ethType": "0x0800"})

        # IP protocol criteria
        if protocol == 'tcp':
            criteria.append({"type": "IP_PROTO", "protocol": 6})
            if direction == 'src':
                criteria.append({"type": "ETH_SRC", "mac": self.src_mac})
                criteria.append({"type": "TCP_SRC", "tcpPort": self.client_port})
            elif direction == 'dst':
                criteria.append({"type": "ETH_DST", "mac": self.dst_mac})
                criteria.append({"type": "TCP_DST", "tcpPort": self.client_port})
        elif protocol == 'udp':
            criteria.append({"type": "IP_PROTO", "protocol": 17})
            if direction == 'src':
                criteria.append({"type": "ETH_SRC", "mac": self.src_mac})
                criteria.append({"type": "UDP_SRC", "udpPort": self.client_port})
            elif direction == 'dst':
                criteria.append({"type": "ETH_DST", "mac": self.dst_mac})
                criteria.append({"type": "UDP_DST", "udpPort": self.client_port})

        # Common criteria: Incoming port
        criteria.append({"type": "IN_PORT", "port": self._get_inbound_port(direction)})
        print("Constructed flow rule: %s", rule)
        return rule

    def _get_output_port(self, direction):
        """Return the appropriate OUTPUT port based on flow direction."""
        if direction == 'src':
            return self.outbound_port_src
        elif direction == 'dst':
            return self.outbound_port_dst

    def _get_inbound_port(self, direction):
        """Return the appropriate IN_PORT based on flow direction."""
        if direction == 'src':
            return self.inbound_port_src
        elif direction == 'dst':
            return self.inbound_port_dst

    def _send_flow_rule_request(self, flow_rule, url):
        """Sends a flow rule POST request and extracts flow IDs from the JSON response."""
        flow_ids = []
        rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))
        if rsp.ok:
            try:
                flow_info = rsp.json()  # e.g., {"flows": [{"deviceId": "...", "flowId": "..."}, ...]}
                for flow in flow_info.get("flows", []):
                    flow_id = flow.get("flowId")
                    if flow_id is not None:
                        flow_ids.append(flow_id)
            except (ValueError, KeyError):
                print("Failed to parse flow response.")
        else:
            print("Error Response:", rsp.text)
        return flow_ids

    def make_flow_adjustment(self):
        app_id = 'ai.classifier.ratelimiter'
        url = f'http://{self.controller_ip}:8181/onos/v1/flows?appId={app_id}'

        # Convert the meter_id to a proper numeric value
        try:
            numeric_meter_id = convert_onos_meter_api_id_to_internal_id(self.meter_id)
            print('### CONVERTED METER ID', self.meter_id, 'to', numeric_meter_id)
        except ValueError as e:
            print(f"Meter ID conversion error: {e}")
            return []

        flow_ids = []
        if self.protocol == 'tcp':
            # Build flow rules for TCP: one for source criteria, one for destination criteria.
            flow_rule_src = self._build_flow_rule('tcp', 'src', numeric_meter_id)
            flow_rule_dst = self._build_flow_rule('tcp', 'dst', numeric_meter_id)
            flow_ids.extend(self._send_flow_rule_request(flow_rule_src, url))
            flow_ids.extend(self._send_flow_rule_request(flow_rule_dst, url))
        else:
            # Build flow rules for UDP: one for source and one for destination.
            flow_rule_src = self._build_flow_rule('udp', 'src', numeric_meter_id)
            flow_rule_dst = self._build_flow_rule('udp', 'dst', numeric_meter_id)
            flow_ids.extend(self._send_flow_rule_request(flow_rule_src, url))
            flow_ids.extend(self._send_flow_rule_request(flow_rule_dst, url))

        return {
            "flow_ids": flow_ids,
            "flow_rule_src": flow_rule_src,
            "flow_rule_dst": flow_rule_dst
        }
