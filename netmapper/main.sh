#!/bin/bash

# Run the first Python script
echo "##################### Running AutoDiscovery Script ##################"
python3 autodiscover.py
echo "Auto Discovery Completed"

#use this below command if installing from the same server (comment the remote server command)
#-------------------------------------------------------------------------

#systemctl restart zabbix-server

#-------------------------------------------------------------------------

#only use this below part if installing from a remote server (comment the same server command)
#--------------------------------------------------------------------------

echo "############### Restarting Zasya Services #####################"
expect restart-server.exp

echo "Zasya Services Restarted"

#--------------------------------------------------------------------------

#wait for 2 minutes for data to be fetched after restart


echo "################## Waiting for Data to be Fetched for Graphing ##############"

sleep 120

# Run the second Python script
echo "################ Running Auto Network Mapper Script ##################"
python3 netmapscript.py
echo "Network Map Created. Please arrange the map to your suitable topology and perform any other manual changes to your liking !!"

