#!/bin/bash

echo "Hello! To configure ... we will ask you a handful of questions..."

while :; do

  read -r -p 'Set Admin Password (Default zabbix): ' adminPass
  read -r -p 'Network Subnet (Default 192.168.0.0/24): ' subnetCIDR

  read -r -p 'Save? (type "s" to save and exit): '
  [[ "${REPLY}" == 's' ]] && break

done 
