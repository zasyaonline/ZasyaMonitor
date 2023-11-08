LINUX_VERSION = "ubuntu/jammy64"
$default_network_interface = `ip route | awk '/^default/ {printf "%s", $5; exit 0}'`

Vagrant.configure("2") do |config|

    config.vm.network "public_network", bridge: "#$default_network_interface"

    #config.vm.network "private_network", ip: "192.168.56.56"

    config.vm.synced_folder ".", "/vagrant"
    config.disksize.size = '40GB'
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

    config.vm.define "monitor" do |zasya|

      zasya.vm.box = LINUX_VERSION
      zasya.vm.hostname = "monitor"
      #zasya.vm.network "forwarded_port", guest: 80 , host: 8080, host_ip: "127.0.0.1"
      #zasya.vm.network "forwarded_port", guest: 5432 , host: 5432, host_ip: "127.0.0.1"
      #zasya.vm.network "forwarded_port", guest: 10050 , host: 10050, host_ip: "127.0.0.1"
      #zasya.vm.network "forwarded_port", guest: 10051 , host: 10051, host_ip: "127.0.0.1"
	  
      zasya.vm.provision "shell", path: "zabbix-vagrant-install.sh"

    end
  
end
