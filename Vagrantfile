LINUX_VERSION = "ubuntu/jammy64"

Vagrant.configure("2") do |config|

    config.vm.provider "virtualbox" do |vb|
      # Display the VirtualBox GUI when booting the machine
      vb.gui = true
      vb.memory = 4096
      vb.cpus = 3
    end

    # set auto_update to false, if you do NOT want to check the correct
    # additions version when booting this machine
    config.vbguest.auto_update = true
    # do NOT download the iso file from a webserver
    config.vbguest.no_remote = false

    config.vm.define "zasya" do |zasya|

      zasya.vm.box = LINUX_VERSION
      zasya.disksize.size = '10GB'
      zasya.vm.hostname = "zasya-monitor"
      #zasya.vm.network "forwarded_port", guest: 80 , host: 8080, host_ip: "127.0.0.1"
      #zasya.vm.network "forwarded_port", guest: 5432 , host: 5432, host_ip: "127.0.0.1"
      #zasya.vm.network "forwarded_port", guest: 10050 , host: 10050, host_ip: "127.0.0.1"
      #zasya.vm.network "forwarded_port", guest: 10051 , host: 10051, host_ip: "127.0.0.1"
	  
      zasya.vm.provision "shell", path: "zabbix-install.sh"

    end
  
end
