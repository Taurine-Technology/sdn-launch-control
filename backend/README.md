# sdn-launch-control-internal
Internal SDN Launch Control Backend Repo

## Environment variables and automatically generated data
- A default user is created using the values from your environment variable file. If this field is not provided the default user name and password is admin.
- The provided plugins are added to the database
- The available machine learning models are added to the database.

## Running the code
1. Populate an env file using the variables in the [.env.example](./control_center/.env.example) file.
2. Run the automated set up script `./setup.sh`


> [!WARNING]
> Closed-source commercial usage of sdn-launch-control-backend is not permitted with the GPL-3.0. If that license is not compatible with your use case, please contact keeganwhite@taurinetech.com to buy a commercial license.


