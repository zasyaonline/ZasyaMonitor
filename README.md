# Setup

```
$ sudo apt-get install virtualbox vagrant virtualbox-guest-x11 virtualbox-guest-utils
$ vagrant plugin install vagrant-vbguest vagrant-scp vagrant-disksize
```

# How To

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
