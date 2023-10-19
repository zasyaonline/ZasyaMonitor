#!/bin/bash

echo "Hello! To configure ... we will ask you a handful of questions..."

echo -n "New account name (administrator): "
read -r accountName
echo -n "New account password : "
read -r accountPass
echo -n "Subnets for autodiscovery? (192.168.1-255.1-255,10.0.0.1-255,172.16-31.1-255.1-255): "
read -r subNet
echo -n "Enable SNMP? (Y/n) :"
read -y enableSNMP
echo -n "Version 1, 2 or 3? (3) :"
read -y snmpVersion
echo -n "Community string? (rocommunity): "
read -y communityString

echo

if [ -n "$accountName" ]; then
  if [ -n "$accountPass" ]; then
    echo "Setting up account with provided password..."
      if [ -n "$subNet" ]; then
        echo "Setting subnet for autodiscovery..."
      else
        echo "Invalid subnet provided; not setting one."
        if [ -n "$enableSNMP" ]; then
          echo "Enabling SNMP..."
          if [ -n "$snmpVersion" ]; then
            echo "... version ${snmpVersion} SNMP..."
          else
            echo "Invalid SNMP version, skipping..."
          fi
        else
          echo "Not enabling SNMP..."
        fi
      fi
  else
    echo "Invalud or missing password! Exiting."
  fi
else
    echo "Invalud username, password or subnet! Exiting."
fi

echo
echo -n "Press any key to exit..."
read -r exit

