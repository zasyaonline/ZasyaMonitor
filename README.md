# Setup

To build a new instance with Vagrant, you will need:
```
$ sudo apt-get install virtualbox vagrant virtualbox-guest-x11 virtualbox-guest-utils
$ vagrant plugin install vagrant-vbguest vagrant-scp vagrant-disksize
```

Once deployed, find the Zabbix agent at one of the following locations:

- http://localhost/agents/zabbix_agent-6.0.3-linux-4.12-ppc64le-static.tar.gz
- http://localhost/agents/zabbix_agent-6.4.8-windows-amd64-openssl.zip

These are also available via the IP address over the network.

# Installing on Bare Ubuntu

Download https://github.com/zasyaonline/ZasyaMonitor/archive/refs/heads/main.zip ...

Then, copy it to /root/ on the host 
make sure there is already an 'ubuntu' account. 
else create a regular user "ubuntu"
Then:
```
# cd ZasyaMonitor
# ./zabbix-ubuntu-install.sh
```

# Building a New Instance

1. Destroy the current VM:

```
$ vagrant destroy 
```
2. Shut down the current VM:

```
$ vagrant halt
==> zabbix: Attempting graceful shutdown of VM...
```
4. Provision a new VM or start an existing VM: 

```
$ vagrant up
```
5. Use VBoxManage to export the VM disk to a raw formatted disk file:

```
$ VBoxManage clonehd --format RAW ~/VirtualBox\ VMs/ZasyaMonitor_zasya_1699169990933_90363/packer-ubuntu-22.04-x86_64-disk001.vdi ~/Zasya-Monitor-Customer-release.img
0%...10%...20%...30%...40%...50%...60%...70%...80%...90%...100%
Clone medium created in format 'RAW'. UUID: a7e581cb-79ac-409c-b0cb-e8ad91175cff
```

5. Use `dd` to write the raw disk image file to an external disk (your `if` and `of` will differ):

```
$ sudo dd if=$HOME/Zasya-Monitor-Customer-release.img of=/dev/sdc status=progress bs=64K conv=noerror,sync
```

# Customizing an Instance

1. Changing the application name from Zasya to something else, open zabbix-vagrant-install.sh and/or zabbix-ubuntu-install.sh and replace 'Zasya' and 'zasya' with something else (*including the file names!*):
```
# Finish rebranding Zabbix to Zasya
sudo find /usr/share/zabbix/ -type f -not -path './conf/*' -exec sed -i 's/zabbix/zasya/g' {
} \;
sudo find /usr/share/zabbix/ -type f -not -path './conf/*' -exec sed -i 's/Zabbix/Zasya/g' {
} \;
sudo mv /usr/share/zabbix/include/classes/server/CZabbixServer.php /usr/share/zabbix/include/classes/server/CZasyaServer.php
sudo mv /usr/share/zabbix/include/classes/api/item_types/CItemTypeZabbix.php /usr/share/zabbix/include/classes/api/item_types/CItemTypeZasya.php
sudo mv /usr/share/zabbix/include/classes/api/item_types/CItemTypeZabbixActive.php /usr/share/zabbix/include/classes/api/item_types/CItemTypeZasyaActive.php
sudo mv /usr/share/zabbix/zabbix.php /usr/share/zabbix/zasya.php
sudo mv /usr/share/zabbix/conf/zabbix.conf.php /usr/share/zabbix/conf/zasya.conf.php 
```
Then, edit the following line to change the site name:

```
\$ZBX_SERVER_NAME = "Zasya Monitor";
```

2. To change the logos, replace these files:
```
$ ls assets
brand.conf.php                         company-main-logo-sidebar.png  zasya-logo.jpg
company-main-logo.png                  desktop-background.jpeg
company-main-logo-sidebar-compact.png  favicon.ico
 
```

3. Saving changes to the desktop:
```
$ ./save-desktop.sh 
```

4. Saving changes to Zabbix:
```
$ ./save-database.sh 
```

5. Changing disk/filesystem size (Vagrant only): edit the Vagrantfile and adjust the size:
```
config.disksize.size = '10GB'
```
10GB is the default. It cannot be decreased any further.

6. Changing the passwords: at the top of zabbix-vagrant-install.sh and zabbix-ubuntu-install.sh the configurable passwords are here:
```
USERPASSWORD=${1:-CUSTOMPASSWORD}
ADMINPASSWORD=${1:-CUSTOMADMINPASSWORD}
ZABBIX_ADMIN_PASS=${1:-CUSTOM_ZABBIX_ADMIN_PASS}
PGPASSWORD=${1:-CUSTOM_PGPASSWORD}
```
Simply replace 'CUSTOMPASSWORD' or similar with the password that you want to be set upon provision.
