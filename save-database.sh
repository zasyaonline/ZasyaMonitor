#!/bin/bash

# This script is meant to copy the running home directory of the default user
# into the repository (outside of the VM) to save it as the default for future
# versions.

vagrant ssh -- -t "sudo su - postgres -c 'pg_dump zabbix' > /tmp/zabbix.sql"
vagrant scp :/tmp/zabbix.sql zabbix.sql
