#!/bin/sh

echo "To install required packages"
apt-get update
apt-get install -y vsftpd
apt-get install -y zip unzip
apt-get install -y crontab
apt-get install -y mosquitto python-pip
pip install paho-mqtt python-etcd pyserial
pip install --user pymysql
pip install --user natsort
pip install --user crcmod
echo "To add system id 05 and key to database"
mysql -uroot -p123456 lora -e "delete from table_netid where netid_group='05'"
mysql -uroot -p123456 lora -e "insert into table_netid values ('05','05000000','05ffffff','1000','BA21C6216312C334597D88711D9EFABE','BA21C6216312C334597D88711D9EFABE');"

echo "To kill check_repeater.sh inq.py and deq.py process"
killall check_repeater.sh
killall inq.py deq.py

echo "To install lora_repeater packages"
cd /mnt/data/LoRaRepeater
cp lora_repeater_starter /etc/init.d/
chmod 755 /mnt/data/LoRaRepeater/inq.py /mnt/data/LoRaRepeater/deq.py /mnt/data/LoRaRepeater/check_repeater.sh /etc/init.d/lora_repeater_starter
update-rc.d -f lora_repeater_starter remove;
update-rc.d lora_repeater_starter defaults 99;
cd /mnt/data/LoRaRepeater/FTP_config
cp *.* /etc/
mkdir /mnt/data/Ftpdir
cd /mnt/data/Ftpdir
rm repeater_upgrade.zip
userdel -r gemtek
useradd -d /mnt/data/Ftpdir -s /usr/sbin/nologin gemtek
echo -e 'gemtek123\ngemtek123\n' | sudo passwd gemtek
chown gemtek:gemtek /mnt/data/Ftpdir
service vsftpd restart
echo "Finished: /etc/init.d/lora_repeater_starter start or reboot wil be run";
