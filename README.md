# SDN Launch Control AKA Launch Control
Install, manage and do everything Open vSwitch and SDN.

Launch Control is a central management tool for software defined networking (SDN) built to enable easy and automated adoption/installation of the SDN paradigm into new or pre-existing networks.

## Running this code

### Dependencies
Ansible, community.general ansible galaxy collection, Python requirements in requirements.txt. Install it via:
```./install.sh```

Or manually:
```
ansible-galaxy collection install community.general
pip install -r requirements.txt
```

### Running from Source
1. Install the dependencies.
2. Navigate to the [backend folder](backend/control_center) to start the Django server, make the necessary migrations and create an admin user:
```
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
3. Navigate the [frontend folder](ui/control-center) to install the UI packages and start the frontend:
```
npm install
npm start
```
5. Navigate to the UI [here](http://localhost:3000) and the backend [here](http://127.0.0.1:8000/admin).
