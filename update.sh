#!/bin/sh
echo "To install lora_repeater packages"
cd /mnt/data/LoRaRepeater
git pull --rebase
cp lora_repeater_starter /etc/init.d/
chmod 755 /mnt/data/LoRaRepeater/inq.py /mnt/data/LoRaRepeater/deq.py /mnt/data/LoRaRepeater/check_repeater.sh /etc/init.d/lora_repeater_starter
update-rc.d lora_repeater_starter remove;
update-rc.d lora_repeater_starter defaults 99;

echo "Finished: lora_repeater_stater start or reboot wil be run";
