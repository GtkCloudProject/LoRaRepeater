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
cd /mnt/data/LoRaRepeater
cp lora_repeater_starter /etc/init.d/
chmod 755 /mnt/data/LoRaRepeater/inq.py /mnt/data/LoRaRepeater/deq.py /mnt/data/LoRaRepeater/check_repeater.sh /etc/init.d/lora_repeater_starter
update-rc.d -f lora_repeater_starter remove;
update-rc.d lora_repeater_starter defaults 99;

echo "Finished: lora_repeater_stater start or reboot wil be run";
