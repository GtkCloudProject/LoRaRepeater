#!/bin/sh

echo "To install required packages"
apt-get update
apt-get install -y mosquitto python-pip
pip install paho-mqtt python-etcd pyserial
pip install --user pymysql
pip install --user natsort

echo "To add system id 05 and key to database"
mysql -uroot -p123456 lora -e "insert into table_netid values ('05','05000000','05ffffff','1000','BA21C6216312C334597D88711D9EFABE','BA21C6216312C334597D88711D9EFABE');"

echo "To install lora_repeater packages"
sh /mnt/data/LoRaRepeater/update.sh

echo "Finished: lora_repeater_stater start or reboot wil be run";
