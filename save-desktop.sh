#!/bin/bash

# This script is meant to copy the running home directory of the default user
# into the repository (outside of the VM) to save it as the default for future
# versions.

vagrant ssh -- -t 'sudo rm -rf /vagrant/ubuntu; sudo cp -a /home/ubuntu /vagrant/'
zip -r ubuntu.zip ubuntu/
rm -rf ubuntu/
