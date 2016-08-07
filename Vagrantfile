Vagrant.configure(2) do |config|
  config.vm.synced_folder ".", "/neubot-server"
  config.vm.define "jessie64" do |jessie64|
    jessie64.vm.box = "debian/contrib-jessie64"
    jessie64.vm.provider "virtualbox" do |v|
      v.memory = 2048
    end
    jessie64.vm.provision "shell", inline: <<-SHELL
      sudo apt-get install -y git golang
      echo "Now run:"
      echo "1. vagrant ssh"
      echo "2. cd /neubot-server"
      echo "3. sudo ./bin/neubot-server-dev # possibly add -dv"
    SHELL
  end
end
