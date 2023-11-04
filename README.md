# Setup

```
$ sudo apt-get install virtualbox vagrant virtualbox-guest-x11 virtualbox-guest-utils
$ vagrant plugin install vagrant-vbguest vagrant-scp vagrant-disksize
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
$ VBoxManage clonehd --format RAW ~/VirtualBox\ VMs/ZasyaMonitor_zasya_1697694371566_46745/ubuntu-jammy-22.04-cloudimg.vdi Zasya-Monitor-Customer-release.img
```

5. Use `dd` to write the raw disk image file to an external disk (your `if` and `of` will differ):

```
$ dd if=~/Zasya-Monitor-Customer-release.img of=/dev/sdb
```

# Customizing an Instance

1. Changing the application name from Zasya to something else:
```
$ vagrant destroy 
```

2. Changing the logos:
```
$ vagrant destroy 
```

3. Saving changes to the desktop:
```
$ vagrant destroy 
```

4. Saving changes to Zabbix:
```
$ vagrant destroy 
```

5. Changing disk/filesystem size:
```
$ vagrant destroy 
```


