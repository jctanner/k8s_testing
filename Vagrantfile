# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  config.vm.synced_folder ".", "/vagrant", type: "nfs", nfs_udp: false

  config.vm.define "dns1" do |dns1|
    dns1.vm.box = "generic/ubuntu2204"
    dns1.vm.hostname = "dns1.okdlab.net"
  end

  config.vm.define "haproxy" do |haproxy|
    haproxy.vm.box = "generic/ubuntu2204"
    haproxy.vm.hostname = "haproxy.okdlab.net"
  end

  config.vm.define "controlplane1" do |controlplane1|
    controlplane1.vm.box = "generic/ubuntu2204"
    controlplane1.vm.hostname = "controlplane1.okdlab.net"
  end

  config.vm.define "controlplane2" do |controlplane2|
    controlplane2.vm.box = "generic/ubuntu2204"
    controlplane2.vm.hostname = "controlplane2.okdlab.net"
  end

  config.vm.define "controlplane3" do |controlplane3|
    controlplane3.vm.box = "generic/ubuntu2204"
    controlplane3.vm.hostname = "controlplane3.okdlab.net"
  end

  config.vm.define "worker1" do |worker1|
    worker1.vm.box = "generic/ubuntu2204"
    worker1.vm.hostname = "worker1.okdlab.net"
  end

  config.vm.define "worker2" do |worker2|
    worker2.vm.box = "generic/ubuntu2204"
    worker2.vm.hostname = "worker2.okdlab.net"
  end

  config.vm.define "worker3" do |worker3|
    worker3.vm.box = "generic/ubuntu2204"
    worker3.vm.hostname = "worker3.okdlab.net"
  end

  config.vm.provision "shell", inline: <<-SHELL
    #sudo apt-get update && sudo apt-get install -y vim
    #sudo apt-get update && sudo apt-get install -y docker.io
    #sudo apt-get update && sudo apt-get install -y haproxy
  SHELL

end
