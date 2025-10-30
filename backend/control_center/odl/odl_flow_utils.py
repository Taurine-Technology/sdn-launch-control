import json
import logging
import requests
from requests.auth import HTTPBasicAuth
import time
import hashlib

logger = logging.getLogger(__name__)
class OdlMeterFlowRule:
    def __init__(self, protocol_str, client_port_num,
                 in_port_of_number_client_to_server, out_port_of_number_client_to_server,
                 in_port_of_number_server_to_client, out_port_of_number_server_to_client,
                 client_mac_address, server_mac_address, category_obj_cookie,
                 controller_ip_str, odl_meter_id_numeric, odl_switch_node_id_str,
                 flow_priority=60000, flow_timeout_seconds=360, table_id=0): # Added table_id

        self.protocol_str = protocol_str.lower() # 'tcp' or 'udp'
        self.client_port_num = int(client_port_num)

        # Client to Server direction (e.g., client uploads, sends request)
        self.in_port_c2s = str(in_port_of_number_client_to_server) # OpenFlow port number
        self.out_port_c2s = str(out_port_of_number_client_to_server)

        # Server to Client direction (e.g., server responds, client downloads)
        self.in_port_s2c = str(in_port_of_number_server_to_client)
        self.out_port_s2c = str(out_port_of_number_server_to_client)

        self.client_mac_address = client_mac_address
        self.server_mac_address = server_mac_address # MAC of the "other end" if known/needed

        self.controller_ip_str = controller_ip_str
        self.odl_meter_id_numeric = int(odl_meter_id_numeric)
        self.odl_switch_node_id_str = odl_switch_node_id_str
        self.category_obj_cookie = category_obj_cookie

        self.flow_priority = int(flow_priority)
        self.flow_timeout_seconds = int(flow_timeout_seconds) # Idle timeout
        self.table_id = int(table_id)

        # For generating unique flow IDs (can be more sophisticated)
        # Using a simple scheme for now. Ensure these are unique per table per switch.
        self.flow_id_c2s = f"metered-{self.protocol_str}-c2s-{self.client_mac_address}-{self.client_port_num}-m{self.odl_meter_id_numeric}"
        self.flow_id_s2c = f"metered-{self.protocol_str}-s2c-{self.client_mac_address}-{self.client_port_num}-m{self.odl_meter_id_numeric}"

        self.flow_id_c2s, self.flow_id_s2c = self._generate_flow_ids()

    def _generate_flow_ids(self):
        timestamp_ns = time.time_ns()

        # --- Flow ID Generation (unique per flow instance) ---
        base_flow_id_seed_part = (
            f"{self.odl_switch_node_id_str}-"
            f"{self.client_mac_address}-{self.client_port_num}-"
            f"{self.protocol_str}-m{self.odl_meter_id_numeric}"
        )
        seed_c2s = f"{timestamp_ns}-{base_flow_id_seed_part}-c2s"
        seed_s2c = f"{timestamp_ns}-{base_flow_id_seed_part}-s2c"

        hasher_c2s = hashlib.sha1(seed_c2s.encode('utf-8'))
        hex_digest_c2s = hasher_c2s.hexdigest()
        hasher_s2c = hashlib.sha1(seed_s2c.encode('utf-8'))
        hex_digest_s2c = hasher_s2c.hexdigest()

        flow_id_c2s_str = f"flow-c2s-{hex_digest_c2s[:8]}"
        flow_id_s2c_str = f"flow-s2c-{hex_digest_s2c[:8]}"

        return flow_id_c2s_str, flow_id_s2c_str

    def _build_odl_flow_payload(self, flow_id_str, direction_str):
        """
        Constructs the JSON payload for an OpenDaylight flow rule.
        direction_str: 'c2s' (client-to-server) or 's2c' (server-to-client)
        """
        match_criteria = {
            "ethernet-match": {
                "ethernet-type": {"type": 0x0800} # IPv4
            }
        }
        # Common IP Protocol
        if self.protocol_str == 'tcp':
            match_criteria["ip-match"] = {"ip-protocol": 6}
        elif self.protocol_str == 'udp':
            match_criteria["ip-match"] = {"ip-protocol": 17}
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol_str}")

        # Direction-specific match criteria
        if direction_str == 'c2s': # Client is source
            match_criteria["in-port"] = self.in_port_c2s
            if self.client_mac_address:
                 match_criteria["ethernet-match"]["ethernet-source"] = {"address": self.client_mac_address}
            # if self.server_mac_address: # Typically match on destination MAC if known
            #      match_criteria["ethernet-match"]["ethernet-destination"] = {"address": self.server_mac_address}

            if self.protocol_str == 'tcp':
                match_criteria["tcp-source-port"] = self.client_port_num
            elif self.protocol_str == 'udp':
                match_criteria["udp-source-port"] = self.client_port_num
            output_port_for_action = self.out_port_c2s
        elif direction_str == 's2c': # Client is destination
            match_criteria["in-port"] = self.in_port_s2c
            if self.client_mac_address: # Traffic returning to the client
                 match_criteria["ethernet-match"]["ethernet-destination"] = {"address": self.client_mac_address}
            # if self.server_mac_address: # Traffic coming from the server
            #      match_criteria["ethernet-match"]["ethernet-source"] = {"address": self.server_mac_address}

            if self.protocol_str == 'tcp':
                match_criteria["tcp-destination-port"] = self.client_port_num
            elif self.protocol_str == 'udp':
                match_criteria["udp-destination-port"] = self.client_port_num
            output_port_for_action = self.out_port_s2c
        else:
            raise ValueError(f"Invalid direction: {direction_str}")

        flow_payload = {
            "flow-node-inventory:flow": [{
                "id": flow_id_str,
                "table_id": self.table_id,
                "priority": self.flow_priority,
                "idle-timeout": self.flow_timeout_seconds,
                "cookie": self.category_obj_cookie,
                "flow-name": f"name-{flow_id_str}",
                "match": match_criteria,
                "instructions": {
                    "instruction": [
                        {"order": 0, "apply-actions": {"action": [
                            {"order": 0, "output-action": {"output-node-connector": output_port_for_action}}
                        ]}},
                        {"order": 1, "meter": {"meter-id": self.odl_meter_id_numeric}}
                    ]
                }
            }]
        }

        return flow_payload

    def _send_flow_to_odl(self, flow_payload, flow_id_str, controller_device_obj):
        """
        Sends a single flow rule to OpenDaylight.
        Uses PUT (create or replace).
        """
        # Use the RFC 8040 URL
        # URL: /rests/data/opendaylight-inventory:nodes/node=<Node-id>/flow-node-inventory:table=<Table-#>/flow=<Flow-#>
        # self.odl_switch_node_id_str is already "openflow:123..."
        api_url = (
            f"http://{self.controller_ip_str}:8181/rests/data/"
            f"opendaylight-inventory:nodes/node={self.odl_switch_node_id_str}/"
            f"flow-node-inventory:table={self.table_id}/flow={flow_id_str}"
        )

        # print(f"Sending ODL flow rule to: {api_url}")
        # print(f"ODL Flow Payload for {flow_id_str}: {json.dumps(flow_payload)}")

        try:
            response = requests.put(
                api_url,
                json=flow_payload,
                auth=HTTPBasicAuth('admin', 'admin'),
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                timeout=15
            )
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            # print(f"Successfully programmed ODL flow {flow_id_str}. Status: {response.status_code}")
            return {"status": "success", "flow_id": flow_id_str, "response_code": response.status_code, "payload_sent": flow_payload}
        except requests.exceptions.HTTPError as e:
            err_msg = f"Failed to program ODL flow {flow_id_str}. Status: {e.response.status_code}. Response: {e.response.text}"
            logger.exception(err_msg)
            return {"status": "error", "flow_id": flow_id_str, "message": err_msg, "response_code": e.response.status_code}
        except requests.exceptions.RequestException as e:
            err_msg = f"Network error while programming ODL flow {flow_id_str}: {e}"
            logger.exception(err_msg)
            return {"status": "error", "flow_id": flow_id_str, "message": err_msg}


    def apply_metered_flow_rules(self, controller_device_obj):
        """
        Builds and sends flow rules for both directions (client-to-server and server-to-client)
        to OpenDaylight.
        controller_device_obj: The general.models.Device instance for the ODL controller.
        """
        results = []
        payload_c2s = self._build_odl_flow_payload(self.flow_id_c2s, 'c2s')
        result_c2s = self._send_flow_to_odl(payload_c2s, self.flow_id_c2s, controller_device_obj)
        results.append(result_c2s)

        # Only proceed to s2c if c2s was successful, or handle errors appropriately
        if result_c2s.get("status") == "success":
            payload_s2c = self._build_odl_flow_payload(self.flow_id_s2c, 's2c')
            result_s2c = self._send_flow_to_odl(payload_s2c, self.flow_id_s2c, controller_device_obj)
            results.append(result_s2c)
        else:
            logger.debug(f"Skipping s2c flow for {self.flow_id_c2s} due to previous error.")
            results.append({"status": "skipped", "flow_id": self.flow_id_s2c, "reason": "c2s flow failed"})

        return results