#!/bin/bash

echo "Hello! To configure ... we will ask you a handful of questions..."

echo -n "New account name: "
read -r accountName
echo -n "New account password: "
read -r accountPass
echo -n "Subnet for autodiscovery? (192.168.0.0/24): "
read -r subNet


if [ -n "$accountName" ]; then
  if [ -n "$accountPass" ]; then
    echo "Setting up account with provided password..."
      if [ -n "$subNet" ]; then
        echo "Setting subnet for autodiscovery..."
      else
        echo "Invalid subnet provided; not setting one."
      fi
  else
    echo "Invalud or missing password! Exiting."
  fi
else
    echo "Invalud username, password or subnet! Exiting."
fi


