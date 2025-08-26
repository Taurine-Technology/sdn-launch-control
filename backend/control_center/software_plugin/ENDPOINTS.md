# 📌 Plugin API Endpoints

This document outlines the available API endpoints for managing **Plugins**, **Plugin Installations**, and **Plugin Requirements** within the SDN Launch Control system.

---

## **🔹 Plugin Management**

| **Method** | **Endpoint**                       | **Description**                       | **Payload (if applicable)**                                                                                                                                                                                                                      |
|------------|------------------------------------|---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **GET**    | `/api/v1/plugins/`                 | List all plugins                      | None                                                                                                                                                                                                                                             |
| **POST**   | `/api/v1/plugins/`                 | Create a new plugin                   | `{ "alias": "tau-sniffer", "name": "Traffic Sniffer", "version": "1.0", "short_description": "Traffic analysis tool", "long_description": "Captures and classifies network traffic", "author": "Keegan White", "requires_target_device": true }` |
| **GET**    | `/api/v1/plugins/{id}/`            | Retrieve details of a specific plugin | None                                                                                                                                                                                                                                             |
| **PUT**    | `/api/v1/plugins/{id}/`            | Update a plugin                       | `{ "name": "Traffic Sniffer", "version": "1.1" }`                                                                                                                                                                                                |
| **DELETE** | `/api/v1/plugins/{id}/`            | Delete a plugin                       | None                                                                                                                                                                                                                                             |
| **POST**   | `/api/v1/plugins/install-sniffer/` | Install Sniffer Plugin on a device    | `{ "lan_ip_address": "192.168.1.10", "api_base_url": "http://api.example.com", "monitor_interface": "eth0", "port_to_client": "2", "port_to_router": "1" }`                                                                                      |

---

## **🔹 Plugin Dependencies**

| **Method** | **Endpoint**                        | **Description**                  | **Payload**                             |
|------------|-------------------------------------|----------------------------------|-----------------------------------------|
| **GET**    | `/api/v1/plugin-requirements/`      | List all plugin dependencies     | None                                    |
| **POST**   | `/api/v1/plugin-requirements/`      | Define a dependency              | `{ "plugin": 1, "required_plugin": 2 }` |
| **GET**    | `/api/v1/plugin-requirements/{id}/` | Retrieve details of a dependency | None                                    |
| **DELETE** | `/api/v1/plugin-requirements/{id}/` | Remove a dependency              | None                                    |

---

## **🔹 Plugin Installations**

| **Method** | **Endpoint**                         | **Description**                     | **Payload**                    |
|------------|--------------------------------------|-------------------------------------|--------------------------------|
| **GET**    | `/api/v1/plugin-installations/`      | List all plugin installations       | None                           |
| **POST**   | `/api/v1/plugin-installations/`      | Install a plugin on a device        | `{ "plugin": 1, "device": 3 }` |
| **GET**    | `/api/v1/plugin-installations/{id}/` | Retrieve details of an installation | None                           |
| **DELETE** | `/api/v1/plugin-installations/{id}/` | Uninstall a plugin from a device    | None                           |

---

## **🔹 Authentication & Security**
- All endpoints require **authentication**.
- Requests should include an **authorization token** in the `Authorization` header.

```http
Authorization: Token <your-auth-token>
```

