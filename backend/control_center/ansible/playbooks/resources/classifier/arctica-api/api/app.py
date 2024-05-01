from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from flask import Flask, request, abort
from flask_jwt_extended import create_access_token
from flask_jwt_extended import JWTManager, jwt_required
from requests.auth import HTTPBasicAuth

from user import create_user_from_json
from classification import create_classification_from_json
import classification_model

import os

# Read environment variables and set defaults if unable to find the values
controller_ip = os.environ.get('CONTROLLER_IP', '127.0.0.1:8181')
websocket_api_url = os.environ.get('WEBSOCKET_API_URL', 'http://10.10.10.2:8000/post_flow_classification/')
google_meter_id = int(os.environ.get('GOOGLE_METER_ID', 2))
social_media_meter_id = int(os.environ.get('SOCIAL_MEDIA_METER_ID', 2))
amazonaws_meter_id = int(os.environ.get('AMAZONAWS_METER_ID', 2))
apple_meter_id = int(os.environ.get('APPLE_METER_ID', 2))
cloudflare_meter_id = int(os.environ.get('CLOUDFLARE_METER_ID', 2))
cybersec_meter_id = int(os.environ.get('CYBERSEC_METER_ID', 2))
http_meter_id = int(os.environ.get('HTTP_METER_ID', 2))
tls_meter_id = int(os.environ.get('TLS_METER_ID', 2))
default_meter_id = int(os.environ.get('DEFAULT_METER_ID', 2))
google_meter_priority = int(os.environ.get('GOOGLE_METER_PRIORITY', 40000))
social_media_meter_priority = int(os.environ.get('SOCIAL_MEDIA_METER_PRIORITY', 40000))
amazonaws_meter_priority = int(os.environ.get('AMAZONAWS_METER_PRIORITY', 40000))
apple_meter_priority = int(os.environ.get('APPLE_METER_PRIORITY', 40000))
cloudflare_meter_priority = int(os.environ.get('CLOUDFLARE_METER_PRIORITY', 40000))
cybersec_meter_priority = int(os.environ.get('CYBERSEC_METER_PRIORITY', 40000))
http_meter_priority = int(os.environ.get('HTTP_METER_PRIORITY', 40000))
tls_meter_priority = int(os.environ.get('TLS_METER_PRIORITY', 40000))
default_meter_priority = int(os.environ.get('DEFAULT_METER_PRIORITY', 40000))

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # token will last for 1 hour
jwt = JWTManager(app)
username = 'arctica'
password = 'arctica'
classifier = classification_model.ClassificationModel('attention-random-model-23-8400', 23)

# allowed_macs = ['04:42:1A:93:57:52']
allowed_ips = ['10.0.0.16', '10.0.0.12', '127.0.0.1', '172.25.0.2']

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["5 per minute", "1000 per second"]
)


# @app.before_request
# def restrict_by_mac():
#     print(request.remote_addr)
#     client_ip = request.remote_addr
#     print(getmac.get_mac_address())
#     if client_ip not in allowed_ips:
#         abort(403)  # Forbidden


@app.route("/login", methods=["POST"])
@limiter.limit('5 per minute')
def login():
    # Validate the request data and get the user
    data = request.get_json()
    user = create_user_from_json(data)
    # If the user exists and the password is correct, return a token
    if user.check_password(password) and user.check_user(username):
        access_token = create_access_token(identity=user.username)
        return {"access_token": access_token}
    else:
        return {"error": "Invalid username or password"}, 401


@app.route("/")
@limiter.limit('5 per minute')
def index():
    return "Hello, World! We picked up the changes."


@app.route("/classify", methods=["POST"])
@jwt_required()
@limiter.limit("30000 per second")
def classify():
    data = request.get_json()
    classification = create_classification_from_json(data)
    result = classifier.predict_flow(classification.payload)
    print(result[0])
    rsp = requests.post(url=websocket_api_url, json=result[0])
    # make_flow_adjustment(result[0], classification.src_mac, classification.src, classification.client_port,
    #                      classification.tcp, classification.switch_id, classification.inbound_port,
    #                      classification.outbound_port)

    return str(result)


def make_flow_adjustment(category, src_mac, src, client_port, tcp, switch_id, inbound_port, outbound_port, vlan='None'):
    """

    :param tcp:
    :param client_port:
    :param outbound_port: the port sending traffic
    :param inbound_port: the port receiving traffic
    :param switch_id:
    :param category:
    :param src_mac:
    :param src: indicates if the src_mac variable is actually the src or dst
    :param vlan:
    :return:
    """
    # print('making flow adjustment')
    app_id = '0x123'
    switch_id = switch_id
    priority = 40000
    # print(category.upper())
    category = category.upper()
    if "GOOGLE" in category:
        meter_id = google_meter_id
        priority = google_meter_priority
    elif category == "WHATSAPP" or category == "FACEBOOK" or category == "INSTAGRAM" or category == "TIKTOK":
        meter_id = social_media_meter_id
        priority = social_media_meter_priority
    elif category == "AMAZONAWS":
        meter_id = amazonaws_meter_id
        priority = amazonaws_meter_priority
    elif category == "APPLE":
        meter_id = apple_meter_id
        priority = apple_meter_priority
    elif category == "CLOUDFLARE":
        meter_id = cloudflare_meter_id
        priority = cloudflare_meter_priority
    elif category == "CYBERSEC":
        meter_id = cybersec_meter_id
        priority = cybersec_meter_priority
    elif category == "HTTP":
        meter_id = http_meter_id
        priority = http_meter_priority
    elif category == "TLS":
        meter_id = tls_meter_id
        priority = tls_meter_priority
    else:
        meter_id = default_meter_id
        priority = default_meter_priority
    print("---------\nMaking flow rule adjustments for category:", category, "with meter ID:", meter_id,
          "and a priority of", priority)
    if tcp == 1:  # this is a tcp flow
        url = 'http://10.8.8.2:8181/onos/v1/flows?appId=' + app_id
        flow_rule = {
            "flows": [
                {
                    "priority": priority,
                    "timeout": 0,
                    "isPermanent": 'true',
                    "deviceId": switch_id,
                    "treatment": {
                        "instructions": [
                            {
                                "type": "OUTPUT",
                                "port": outbound_port
                            },
                            {
                                "type": "METER",
                                "meterId": meter_id
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
                                "mac": src_mac
                            },
                            {
                                "type": "TCP_SRC",
                                "tcpPort": client_port
                            },
                            {
                                "type": "IN_PORT",
                                "port": inbound_port
                            }
                        ]
                    }
                }
            ]
        }
        rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))
        # print(flow_rule)
        # print(rsp.status_code)
        flow_rule = {
            "flows": [
                {
                    "priority": priority,
                    "timeout": 0,
                    "isPermanent": 'true',
                    "deviceId": switch_id,
                    "treatment": {
                        "instructions": [
                            {
                                "type": "OUTPUT",
                                "port": outbound_port
                            },
                            {
                                "type": "METER",
                                "meterId": meter_id
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
                                "mac": src_mac
                            },
                            {
                                "type": "TCP_DST",
                                "tcpPort": client_port
                            },
                            {
                                "type": "IN_PORT",
                                "port": inbound_port
                            }
                        ]
                    }
                }
            ]
        }
        rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))
        # print(flow_rule)
        print(rsp.status_code)
        # print("Phone port is", client_port)

    # {
    #     "type": "TCP_SRC",
    #     "tcpPort": 1
    # },
    # {
    #     "type": "TCP_DST",
    #     "tcpPort": 1
    # },
    elif tcp == 0:  # this is a udp flow

        url = 'http://10.8.8.2:8181/onos/v1/flows?appId=' + app_id
        flow_rule = {
            "flows": [
                {
                    "priority": priority,
                    "timeout": 0,
                    "isPermanent": 'true',
                    "deviceId": switch_id,
                    "treatment": {
                        "instructions": [
                            {
                                "type": "OUTPUT",
                                "port": outbound_port
                            },
                            {
                                "type": "METER",
                                "meterId": meter_id
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
                                "mac": src_mac
                            },
                            {
                                "type": "UDP_SRC",
                                "udpPort": client_port
                            },
                            {
                                "type": "IN_PORT",
                                "port": inbound_port
                            }
                        ]
                    }
                }
            ]
        }
        rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))

        flow_rule = {
            "flows": [
                {
                    "priority": priority,
                    "timeout": 0,
                    "isPermanent": 'true',
                    "deviceId": switch_id,
                    "treatment": {
                        "instructions": [
                            {
                                "type": "OUTPUT",
                                "port": outbound_port
                            },
                            {
                                "type": "METER",
                                "meterId": meter_id
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
                                "mac": src_mac
                            },
                            {
                                "type": "UDP_DST",
                                "udpPort": client_port
                            },
                            {
                                "type": "IN_PORT",
                                "port": inbound_port
                            }
                        ]
                    }
                }
            ]
        }
        # print("Phone port is", client_port)
        # print(flow_rule)
        rsp = requests.post(url=url, json=flow_rule, auth=HTTPBasicAuth('onos', 'rocks'))
        print(flow_rule)

        # {
        #     "type": "UDP_SRC",
        #     "udpPort": 1
        # },
        # {
        #     "type": "UDP_DST",
        #     "udpPort": 1
        # },


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
