import requests
from requests.auth import HTTPBasicAuth


class MeterFlowRule(object):

    def __init__(self, proto, client_port, outbound_port, inbound_port, category, src_mac, controller_ip, meter_id, switch_id):
        self.protocol = proto
        self.client_port = client_port
        self.outbound_port = outbound_port
        self.inbound_port = inbound_port
        self.category = category
        self.src_mac = src_mac
        self.controller_ip = controller_ip
        self.priority = 50000
        self.meter_id = meter_id
        self.switch_id = switch_id
        # get device ID

    def make_flow_adjustment(self):
        app_id = '0x123'
        url = f'http://{self.controller_ip}:8181/onos/v1/flows?appId={app_id}'
        print('*** MAKING FLOW ADJUSTMENT ***')
        if self.protocol == 'tcp':

            flow_rule = {
                "flows": [
                    {
                        "priority": self.priority,
                        "timeout": 0,
                        "isPermanent": 'true',
                        "deviceId": self.switch_id,
                        "treatment": {
                            "instructions": [
                                {
                                    "type": "OUTPUT",
                                    "port": self.outbound_port
                                },
                                {
                                    "type": "METER",
                                    "meterId": self.meter_id
                                }
                            ]
                        },
                        "selector": {
                            "criteria": [
                                {
                                    "type": "ETH_TYPE",
                                    "ethType": "0x0800"
                                },
                                {
                                    "type": "IP_PROTO",
                                    "protocol": 6
                                },
                                {
                                    "type": "ETH_SRC",
                                    "mac": self.src_mac
                                },
                                {
                                    "type": "TCP_SRC",
                                    "tcpPort": self.client_port
                                },
                                {
                                    "type": "IN_PORT",
                                    "port": self.inbound_port
                                }
                            ]
                        }
                    }
                ]
            }

            rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))
            print(rsp)
            flow_rule = {
                "flows": [
                    {
                        "priority": self.priority,
                        "timeout": 0,
                        "isPermanent": 'true',
                        "deviceId": self.switch_id,
                        "treatment": {
                            "instructions": [
                                {
                                    "type": "OUTPUT",
                                    "port": self.outbound_port
                                },
                                {
                                    "type": "METER",
                                    "meterId": self.meter_id
                                }
                            ]
                        },
                        "selector": {
                            "criteria": [
                                {
                                    "type": "ETH_TYPE",
                                    "ethType": "0x0800"
                                },
                                {
                                    "type": "IP_PROTO",
                                    "protocol": 6
                                },
                                {
                                    "type": "ETH_DST",
                                    "mac": self.src_mac
                                },
                                {
                                    "type": "TCP_DST",
                                    "tcpPort": self.client_port
                                },
                                {
                                    "type": "IN_PORT",
                                    "port": self.inbound_port
                                }
                            ]
                        }
                    }
                ]
            }
            rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))
            print(rsp)
        else:
            flow_rule = {
                "flows": [
                    {
                        "priority": self.priority,
                        "timeout": 0,
                        "isPermanent": 'true',
                        "deviceId": self.switch_id,
                        "treatment": {
                            "instructions": [
                                {
                                    "type": "OUTPUT",
                                    "port": self.outbound_port
                                },
                                {
                                    "type": "METER",
                                    "meterId": self.meter_id
                                }
                            ]
                        },
                        "selector": {
                            "criteria": [
                                {
                                    "type": "ETH_TYPE",
                                    "ethType": "0x0800"
                                },
                                {
                                    "type": "IP_PROTO",
                                    "protocol": 17
                                },
                                {
                                    "type": "ETH_SRC",
                                    "mac": self.src_mac
                                },
                                {
                                    "type": "UDP_SRC",
                                    "udpPort": self.client_port
                                },
                                {
                                    "type": "IN_PORT",
                                    "port": self.inbound_port
                                }
                            ]
                        }
                    }
                ]
            }
            rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))
            print(rsp)
            flow_rule = {
                "flows": [
                    {
                        "priority": self.priority,
                        "timeout": 0,
                        "isPermanent": 'true',
                        "deviceId": self.switch_id,
                        "treatment": {
                            "instructions": [
                                {
                                    "type": "OUTPUT",
                                    "port": self.outbound_port
                                },
                                {
                                    "type": "METER",
                                    "meterId": self.meter_id
                                }
                            ]
                        },
                        "selector": {
                            "criteria": [
                                {
                                    "type": "ETH_TYPE",
                                    "ethType": "0x0800"
                                },
                                {
                                    "type": "IP_PROTO",
                                    "protocol": 17
                                },
                                {
                                    "type": "ETH_DST",
                                    "mac": self.src_mac
                                },
                                {
                                    "type": "UDP_DST",
                                    "udpPort": self.client_port
                                },
                                {
                                    "type": "IN_PORT",
                                    "port": self.inbound_port
                                }
                            ]
                        }
                    }
                ]
            }
            rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))
            print(rsp)
