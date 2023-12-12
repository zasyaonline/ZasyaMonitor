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

# Building a New Custom Instance


1. Changing disk/filesystem size (Vagrant only): edit the Vagrantfile and adjust the size:
```
config.disksize.size = '40GB'
```
40GB is the default. It cannot be decreased any further.v

2. Changing the passwords: at the top of zabbix-vagrant-install.sh and zabbix-ubuntu-install.sh the configurable passwords are here:
```
USERPASSWORD=${1:-CUSTOMPASSWORD}
ADMINPASSWORD=${1:-CUSTOMADMINPASSWORD}
ZABBIX_ADMIN_PASS=${1:-CUSTOM_ZABBIX_ADMIN_PASS}
PGPASSWORD=${1:-CUSTOM_PGPASSWORD}
```
Simply replace 'CUSTOMPASSWORD' or similar with the password that you want to be set upon provision.

3. Start from scratch by deleting any existing VM with `vagrant destroy -f`. Also, you can/should remove zabbix.sql to start a new database from scratch since the database contains branded titles and group names.

4. Changing the application name, open zabbix-vagrant-install.sh and replace 'Zasya' and 'zasya' with something else on these two lines:
```
BRANDNAME_UPPER=${1:-Zasya}
BRANDNAME_LOWER=${1:-zasya}
```
5. To change the logos, replace these files:
```
$ ls assets
brand.conf.php                         company-main-logo-sidebar.png  zasya-logo.jpg
company-main-logo.png                  desktop-background.jpeg
company-main-logo-sidebar-compact.png  favicon.ico
```

** How to create to a favicon
https://www.lcn.com/blog/beginners-guide-favicons/


Edit the brand.conf.php:

```
cat assets/brand.conf.php                INT ✘ 
<?php

       return [
           'BRAND_LOGO' => 'company-main-logo.png',
           'BRAND_LOGO_SIDEBAR' => 'company-main-logo-sidebar.png',
           'BRAND_LOGO_SIDEBAR_COMPACT' => 'company-main-logo-sidebar-compact.png',
           'BRAND_FOOTER' => '© 2023 Zasya Online',
           'BRAND_HELP_URL' => 'https://zasyaonline.com/help/'
       ];
```

vagrant up
vagrant ssh
vagrant@monitor:~$ sudo -i
root@monitor:~# cd /vagrant/
root@monitor:/vagrant# ./zabbix-ubuntu-install.sh
6. Run vagrant up and wait for desktop and login.

7. Make customizations to desktop configuration, and then once satisfied proceed to save the desktop and databases.

8. Saving changes to the desktop for future:
```
$ ./save-desktop.sh 
```

9. Saving changes to Zabbix for future use:
```
$ ./save-database.sh 
```

10. Shut down the current VM:

```
$ vagrant halt
==> zabbix: Attempting graceful shutdown of VM...
```
11. Provision a new VM or start an existing VM: 

```
$ vagrant up
```
12. Use VBoxManage to export the VM disk to a raw formatted disk file:

```
$ VBoxManage clonehd --format RAW ~/VirtualBox\ VMs/ZasyaMonitor_zasya_1699169990933_90363/packer-ubuntu-22.04-x86_64-disk001.vdi ~/Zasya-Monitor-Customer-release.img
0%...10%...20%...30%...40%...50%...60%...70%...80%...90%...100%
Clone medium created in format 'RAW'. UUID: a7e581cb-79ac-409c-b0cb-e8ad91175cff
```

13. Use `dd` to write the raw disk image file to an external disk (your `if` and `of` will differ):

```
$ sudo dd if=$HOME/Zasya-Monitor-Customer-release.img of=/dev/sdc status=progress bs=64K conv=noerror,sync
```
