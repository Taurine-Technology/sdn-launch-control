# Controllers

## OpenDayLight
After running the installation of ODL via the UI. You need to install applications to get a basic L2 set up and a UI.
The java home environment variable is set but the device may need to be restarted or the source may need to be manually reset.
This is done as follows:
1. SSH into the VM/Device running ODL
2. Set the source if nothing is shown when you run `echo $JAVA_HOME`:
```
source /etc/environment
```
3. Check that the variable is set now: `echo $JAVA_HOME`. If there is no output insert the following line into your environment file:
```
/usr/lib/jvm/java-8-openjdk-amd64"
```
4. Start ODL by navigating to the installation destination and running Karaf:
```
cd /opt/karaf-0.8.4/bin/
sudo ./karaf
```
5. Install the necessary apps from hte ODL command line: `feature:install odl-restconf-all odl-l2switch-switch odl-mdsal-all features-dlux features-dluxapps`
6. Navigate to the UI at the URL of the VM/Device running ODL for example: 
[http://10.10.10.44:8181/index.html#/node/index](http://10.10.10.44:8181/index.html#/node/index)
where '10.10.10.10' is the IP address of the VM/device. The default username and password is 'admin'.