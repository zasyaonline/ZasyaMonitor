# Setup

```
  ~/S/zasya-monitor  sudo apt-get install virtualbox vagrant 
  ~/S/zasya-monitor  vagrant plugin install vagrant-vbguest --plugin-version 0.21
```

# How To Create a New VM

1. Edit the following locations to customize the installation:

2. 

# How To Write VM to Disk to Run

1. To build a new instance:

```
  ~/S/zasya-monitor  vagrant destroy 
    zabbix: Are you sure you want to destroy the 'zabbix' VM? [y/N] y
==> zabbix: Forcing shutdown of VM...
==> zabbix: Destroying VM and associated drives...
  ~/S/zasya-monitor  vagrant up 
Bringing machine 'zabbix' up with 'virtualbox' provider...
==> zabbix: Importing base box 'ubuntu/jammy64'...
==> zabbix: Matching MAC address for NAT networking...
==> zabbix: Checking if box 'ubuntu/jammy64' version '20230828.0.0' is up to date...
==> zabbix: Setting the name of the VM: zasya-monitor_zabbix_1695436074157_71910
<SNIP>
  ~/S/zasya-monitor  vagrant halt
==> zabbix: Attempting graceful shutdown of VM...
```

2. Now, we need to use VBoxManage to export the VM disks to a raw formatted disk file:

```
$ ls -lh VirtualBox\ VMs/zasya-monitor_zabbix_1694659244539_38888
total 5.5G
drwx------ 1 jch jch   16 Sep 13 22:40 Logs
-rw------- 1 jch jch 192K Sep 13 22:40 ubuntu-jammy-22.04-cloudimg-configdrive.vmdk
-rw------- 1 jch jch 5.5G Sep 13 22:56 ubuntu-jammy-22.04-cloudimg.vmdk
-rw------- 1 jch jch 4.4K Sep 13 22:41 zasya-monitor_zabbix_1694659244539_38888.vbox
-rw------- 1 jch jch 4.4K Sep 13 22:41 zasya-monitor_zabbix_1694659244539_38888.vbox-prev

$ VBoxManage clonehd --format RAW VirtualBox\ VMs/zasya-monitor_zabbix_1694659244539_38888/ubuntu-jammy-22.04-cloudimg.vmdk Zasya-Monitor-Customer-release.img
```

3. Finally, we will use `dd` to write the image file to an external disk to be provided to the end-user/customer:

```

```
