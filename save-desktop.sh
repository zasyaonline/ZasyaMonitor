#!/bin/bash

# This script is meant to copy the running home directory of the default user
# into the repository (outside of the VM) to save it as the default for future
# versions.

vagrant ssh -- -t 'sudo cp -a /home/ubuntu /tmp/'
vagrant ssh -- -t 'cd /tmp; sudo zip -r ubuntu.zip ubuntu/'
vagrant scp :/tmp/ubuntu.zip ubuntu.zip
