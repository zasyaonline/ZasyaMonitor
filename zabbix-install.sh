#!/bin/bash

# XXX: Zasya / ubuntu password
echo 'ubuntu:USERPASSWORD' | sudo chpasswd

# XXX: Zasya Admin / vagrant password
echo 'vagrant:ADMINPASSWORD' | sudo chpasswd

# XXX: User Zabbix username and password monadmin
# ...

PGPASSWORD=${1:-ADMINPASSWORD}

sudo sed -i "s/Ubuntu/Zasya/g" /etc/passwd
sudo sed -i "s/1000:,,,/1000:Zasya Admin,,,/g" /etc/passwd

# Remove end-user from sudo group to prevent root access
sudo deluser ubuntu sudo
sudo deluser ubuntu admin

echo "######################################################################"
echo "                        INSTALL ZABBIX                          "
echo "######################################################################"

echo "########################################################"
echo "Install dependencies"
echo "########################################################"
sudo apt-get -q -y update; sudo apt-get -q -y dist-upgrade
sudo apt-get -q -y install gnupg2 

sudo echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

sudo apt-get -q update
sudo apt-get -q -y install postgresql-15

sudo systemctl enable --now postgresql@15-main

sudo sed -i "s/ident/md5/g" /etc/postgresql/15/main/pg_hba.conf
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/15/main/postgresql.conf
sudo systemctl restart postgresql@15-main

sudo -u postgres psql -c "CREATE USER zabbix WITH ENCRYPTED PASSWORD '${PGPASSWORD}'" 2>/dev/null
sudo -u postgres createdb -O zabbix -E Unicode -T template0 zabbix 2>/dev/null

echo "########################################################"
echo "ZABBIX SERVER"
echo "########################################################"

wget https://repo.zabbix.com/zabbix/6.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.4-1+ubuntu22.04_all.deb
sudo dpkg -i zabbix-release_6.4-1+ubuntu22.04_all.deb

sudo apt-get -q update
sudo apt-get -q -y install zabbix-server-pgsql zabbix-sql-scripts

zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix

sudo sed -i "s/# DBHost=localhost/DBHost=localhost/" /etc/zabbix/zabbix_server.conf
sudo sed -i "s/# DBPassword=/DBPassword=${PGPASSWORD}/" /etc/zabbix/zabbix_server.conf

sudo systemctl enable --now zabbix-server

sudo apt-get -q -y install zabbix-frontend-php php8.1-pgsql zabbix-nginx-conf

echo "php_value[date.timezone] = America/Chicago" >> /etc/php/8.1/fpm/pool.d/zabbix-php-fpm.conf

sudo tee /etc/zabbix/web/zabbix.conf.php <<EOL
<?php
    \$DB["TYPE"] = "POSTGRESQL";
    \$DB["SERVER"] = "localhost";
    \$DB["PORT"] = "5432";
    \$DB["DATABASE"] = "zabbix";
    \$DB["USER"] = "zabbix";
    \$DB["PASSWORD"] = "${PGPASSWORD}";
    \$DB["SCHEMA"] = "";
    \$DB["ENCRYPTION"] = false;
    \$DB["KEY_FILE"] = "";
    \$DB["CERT_FILE"] = "";
    \$DB["CA_FILE"] = "";
    \$DB["VERIFY_HOST"] = false;
    \$DB["CIPHER_LIST"] = "";
    \$DB["VAULT_URL"] = "";
    \$DB["VAULT_DB_PATH"] = "";
    \$DB["VAULT_TOKEN"] = "";
    \$DB["DOUBLE_IEEE754"] = true;
    \$ZBX_SERVER = "localhost";
    \$ZBX_SERVER_PORT = "10051";
    \$ZBX_SERVER_NAME = "zabbix";
    \$IMAGE_FORMAT_DEFAULT = IMAGE_FORMAT_PNG;
EOL

mkdir -p /var/lib/locales/supported.d/
rm -f /var/lib/locales/supported.d/local
cat /usr/share/zabbix/include/locales.inc.php | grep display | grep true | awk '{$1=$1};1' | cut -d"'" -f 2 | sort | xargs -I '{}' bash -c 'echo "{}.UTF-8 UTF-8"' >> /etc/locale.gen
dpkg-reconfigure --frontend noninteractive locales

sudo sed -i "s/#        listen          8080;/        listen 80 default_server;\\n        listen [::]:80 default_server;/" /etc/zabbix/nginx.conf
sudo sed -i "s/#        server_name     example.com;/        server_name _;/" /etc/zabbix/nginx.conf
sudo rm /etc/nginx/sites-available/default
sudo rm /etc/nginx/sites-enabled/default
sudo rm /etc/nginx/conf.d/zabbix.conf
sudo ln -s /etc/zabbix/nginx.conf /etc/nginx/sites-available/default
sudo ln -s /etc/zabbix/nginx.conf /etc/nginx/sites-enabled/default

sudo systemctl enable --now php8.1-fpm
sleep 5
sudo systemctl enable --now nginx
sleep 5
sudo systemctl stop php8.1-fpm
sudo systemctl stop nginx
sleep 5
sudo systemctl start php8.1-fpm
sleep 5
sudo systemctl start nginx

sudo apt-get -q -y install zabbix-agent

systemctl enable --now zabbix-agent

echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" | sudo tee /etc/apt/sources.list.d/timescaledb.list
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/timescaledb.gpg

sudo apt-get -q update
sudo apt-get -q install -y timescaledb-2-postgresql-15=2.10.1~ubuntu22.04

sudo systemctl stop zabbix-server
sudo systemctl stop postgresql

sudo cp /vagrant/postgresql.conf /root/
sudo mv /root/postgresql.conf /etc/postgresql/15/main/postgresql.conf

sudo systemctl start postgresql
sudo -u postgres timescaledb-tune --quiet --yes
echo "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;" | sudo -u postgres psql zabbix 2>/dev/null

cat /usr/share/zabbix-sql-scripts/postgresql/timescaledb.sql | sudo -u zabbix psql zabbix

sudo systemctl start zabbix-server
sleep 5
sudo systemctl restart php8.1-fpm
sleep 5
sudo systemctl restart nginx

sudo cp /vagrant/assets/brand.conf.php /usr/share/zabbix/local/conf/brand.conf.php
sudo cp /vagrant/assets/company-main-logo.png /usr/share/zabbix/company-main-logo.png
sudo cp /vagrant/assets/company-main-logo-sidebar.png /usr/share/zabbix/company-main-logo-sidebar.png
sudo cp /vagrant/assets/company-main-logo-sidebar-compact.png /usr/share/zabbix/company-main-logo-sidebar-compact.png

sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -f install virtualbox-guest-utils virtualbox-guest-x11 virtualbox-guest-x11 apache2-utils 
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -f install xubuntu-desktop firefox

sudo cp /vagrant/assets/desktop-background.jpeg /usr/share/xfce4/backdrops/xubuntu-wallpaper.png

sudo rm /usr/share/applications/xfce4-mail-reader.desktop 

sudo rm -rf /home/ubuntu
sudo cp /vagrant/ubuntu.zip /home/
cd /home/; sudo unzip ubuntu.zip
sudo chown -R ubuntu:ubuntu /home/ubuntu/
sudo rm /home/ubuntu.zip

sed -i "s/allowed_users=.*$/allowed_users=anybody/" /etc/X11/Xwrapper.config
sudo cp /vagrant/apps/zasya-monitor-config.sh /usr/local/bin/
sudo chmod 755 /usr/local/bin/zasya-monitor-config.sh

sudo apt-get remove --purge -q -y libreoffice-base-core cheese-common gdm3 cheese thunderbird software-properties-gtk libreoffice-draw gimp hexchat gigolo libreoffice-impress libreoffice-common transmission-gtk rhythmbox xfburn parole gnome-mines gnome-sudoku
sudo apt-get autoremove --purge -q -y

ZABBIX_ADMIN_PASS=`htpasswd -bnBC 10 "" ${PGPASSWORD} | tr -d ":\n"`
psql postgresql://zabbix:${PGPASSWORD}@localhost --command="update users set passwd = '${ZABBIX_ADMIN_PASS}' where username = 'Admin';" 

sudo VBoxClient --clipboard
sudo VBoxClient --draganddrop
sudo VBoxClient --display
sudo VBoxClient --checkhostversion
sudo VBoxClient --seamless

sudo rm -rf /var/cache/apt/archives/*.deb
sudo shutdown -r now
