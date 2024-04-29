# Classifier API and Classification Model
This repo contains the code to be run on the server that is connected to the ONOS controller.

## Prerequisites
- Nvidia Drivers installed
- Nvidia Container toolkit installed for Docker. See [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) 
for instructions.

## Usage
### API
1. Edit the docker-compose.yml variables as needed. Any traffic category you do not set here will get a default priority
and meter ID that is set in the file as well.
2. Build the Classifier API from the beta/classifier/artica-api folder: 
```
docker-compose up --build
```
2. Run the container:
```
docker-compose up --compatibility
```