#!/bin/bash

BRANDNAME_UPPER=${1:-Zasya}
BRANDNAME_LOWER=${1:-zasya}
USERPASSWORD=${1:-USERPASSWORD}
ADMINPASSWORD=${1:-ADMINPASSWORD}
ZABBIX_ADMIN_PASS=${1:-ZABBIX_ADMIN_PASS}
PGPASSWORD=${1:-PGPASSWORD}

echo "######################################################################"
echo "                        INSTALL ZABBIX                          "
echo "######################################################################"

echo "########################################################"
echo "Install dependencies"
echo "########################################################"
sudo apt-get -q -y update; sudo apt-get -q -y dist-upgrade
sudo apt-get -q -y install gnupg2 python3-pip byobu linux-firmware-nonfree

sudo echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

sudo apt-get -q update
sudo apt-get -q -y install postgresql-14

sudo systemctl enable --now postgresql@14-main

sudo sed -i "s/ident/md5/g" /etc/postgresql/14/main/pg_hba.conf
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/14/main/postgresql.conf
sudo systemctl restart postgresql@14-main

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
sudo apt-get clean

echo "php_value[date.timezone] = " >> /etc/php/8.1/fpm/pool.d/zabbix-php-fpm.conf

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
    \$ZBX_SERVER_NAME = "Monitor";
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
sudo apt-get -q install -y timescaledb-2-postgresql-14
sudo apt-get clean

sudo systemctl stop zabbix-server
sudo systemctl stop postgresql

sudo cp postgresql.conf /root/
sudo mv /root/postgresql.conf /etc/postgresql/14/main/postgresql.conf

sudo systemctl start postgresql
sudo -u postgres timescaledb-tune --quiet --yes
echo "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;" | sudo -u postgres psql zabbix 2>/dev/null

cat /usr/share/zabbix-sql-scripts/postgresql/timescaledb.sql | sudo -u zabbix psql zabbix

sudo systemctl start zabbix-server
sleep 5
sudo systemctl restart php8.1-fpm
sleep 5
sudo systemctl restart nginx

sudo cp -a agents /usr/share/zabbix/

sudo cp assets/brand.conf.php /usr/share/zabbix/local/conf/brand.conf.php
sudo cp assets/company-main-logo.png /usr/share/zabbix/company-main-logo.png
sudo cp assets/company-main-logo-sidebar.png /usr/share/zabbix/company-main-logo-sidebar.png
sudo cp assets/company-main-logo-sidebar-compact.png /usr/share/zabbix/company-main-logo-sidebar-compact.png

sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -f install virtualbox-guest-utils virtualbox-guest-x11 virtualbox-guest-x11 apache2-utils 

sudo apt-get clean
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -f install xubuntu-core 
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -f remove --purge gdm3
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -f install lightdm 
sudo apt-get clean

sudo cp assets/desktop-background.jpeg /usr/share/xfce4/backdrops/xubuntu-wallpaper.png
sudo cp assets/favicon.ico /usr/share/zabbix/favicon.ico

sed -i "s/allowed_users=.*$/allowed_users=anybody/" /etc/X11/Xwrapper.config

sudo apt-get remove --purge -q -y libreoffice-base-core cheese-common gdm3 cheese thunderbird software-properties-gtk libreoffice-draw gimp hexchat gigolo libreoffice-impress libreoffice-common transmission-gtk rhythmbox xfburn parole gnome-mines gnome-sudoku snapd
sudo apt-get autoremove --purge -q -y

# Install non-Snap version of Firefox
# https://askubuntu.com/questions/1399383/how-to-install-firefox-as-a-traditional-deb-package-without-snap-in-ubuntu-22
sudo add-apt-repository -y ppa:mozillateam/ppa
sudo apt-get update

echo '
Package: *
Pin: release o=LP-PPA-mozillateam
Pin-Priority: 1001

Package: firefox
Pin: version 1:1snap1-0ubuntu2
Pin-Priority: -1
' | sudo tee /etc/apt/preferences.d/mozilla-firefox

sudo apt install -q -y firefox

sudo pip install git+https://github.com/unioslo/zabbix-cli.git@master
# Hack to fix Zabbix 6.4 support for zabbix-cli
# https://github.com/unioslo/zabbix-cli/issues/160
sudo sed -i "s/user=user/username=user/g" /usr/local/lib/python3.10/dist-packages/zabbix_cli/pyzabbix.py

sudo rm -rf /home/ubuntu
sudo cp ubuntu.zip /home/
sudo unzip ubuntu.zip -d /home/
sudo cp -a host_templates /home/ubuntu/
sudo chown -R ubuntu:ubuntu /home/ubuntu/
sudo rm /home/ubuntu.zip

# Finish rebranding Zabbix to $BRANDNAME
sudo find /usr/share/zabbix/ -type f -not -path './conf/*' -exec sed -i "s/zabbix/${BRANDNAME_LOWER}/g" {} \;
sudo find /usr/share/zabbix/ -type f -not -path './conf/*' -exec sed -i "s/Zabbix/${BRANDNAME_UPPER}/g" {} \;
sudo find /home/ubuntu/host_templates/ -type f -exec sed -i "s/zabbix/${BRANDNAME_LOWER}/g" {} \;
sudo find /home/ubuntu/host_templates/ -type f -exec sed -i "s/Zabbix/${BRANDNAME_UPPER}/g" {} \;
sudo mv /usr/share/zabbix/include/classes/server/CZabbixServer.php /usr/share/zabbix/include/classes/server/C${BRANDNAME_UPPER}Server.php
sudo mv /usr/share/zabbix/include/classes/api/item_types/CItemTypeZabbix.php /usr/share/zabbix/include/classes/api/item_types/CItemType${BRANDNAME_UPPER}.php
sudo mv /usr/share/zabbix/include/classes/api/item_types/CItemTypeZabbixActive.php /usr/share/zabbix/include/classes/api/item_types/CItemType${BRANDNAME_UPPER}Active.php
sudo mv /usr/share/zabbix/zabbix.php /usr/share/zabbix/${BRANDNAME_LOWER}.php
sudo mv /usr/share/zabbix/conf/zabbix.conf.php /usr/share/zabbix/conf/${BRANDNAME_LOWER}.conf.php

sudo usermod -c "${BRANDNAME_UPPER} Admin" vagrant
echo "vagrant:${ADMINPASSWORD}" | sudo chpasswd
# Ubuntu user already exists in ubuntu/jammy64 VM
sudo usermod -c "${BRANDNAME_UPPER}" -s /bin/bash ubuntu
echo "ubuntu:${USERPASSWORD}" | sudo chpasswd

# If a zabbix.sql exists in this folder let's drop the old zabbix database and import it.
if test -f "${PWD}/zabbix.sql"; then
  sudo cp ${PWD}/zabbix.sql /tmp/
  sudo systemctl stop zabbix-server.service
  sudo su - postgres -c 'dropdb zabbix'
  sudo -u postgres createdb -O zabbix -E Unicode -T template0 zabbix
  sudo su - postgres -c 'psql -d zabbix < /tmp/zabbix.sql'
fi

ZABBIX_ADMIN_PASSHASH=`htpasswd -bnBC 10 "" ${ZABBIX_ADMIN_PASS} | tr -d ":\n"`
psql postgresql://zabbix:${PGPASSWORD}@localhost --command="update users set passwd = '${ZABBIX_ADMIN_PASSHASH}' where username = 'Admin';" 
psql postgresql://zabbix:${PGPASSWORD}@localhost --command="update hosts set name = '${BRANDNAME_UPPER} server' where hostid = '10084';"

