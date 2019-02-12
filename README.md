# lora_repeater

It's Lora Repeater suite runs on Python scriptes, includes:
1. inq.py under /mnt/data/LoRaRepeater/ -- means received Mqtt payload from LoRa Gateway and put it to /var/lora_repeater/queue
2. deq.py under /mnt/data/LoRaRepeater/ -- means repeat send queue's data by its LoRa Node module from /var/lora_repeater_sending -
   - if sent, the payload will be move to /var/lora_repeater/sent
   - if fail, the payload will be move to /var/lora_repeater/fail
   - all data log in /var/lora_repeater/log and its rotate by 10MB.
3. lora_repeater_stater, inq and deq service starter under /etc/init.d/


Installation steps:
 1. sudo su
 2. apt-get update
 3. apt-get install -y git
 4. cd /mnt/data/
 5. git clone https://github.com/GtkCloudProject/LoRaRepeater.git
 6. /mnt/data/LoRaRepeater
 7. git checkout check_repeater.sh;git checkout inq.py;git checkout deq.py
 8. git pull --rebase
 9. sh /mnt/data/LoRaRepeater/install.sh
10. reboot

References:
1. https://stackoverflow.com/questions/7266558/pyserial-buffer-wont-flush
2. http://www.itread01.com/articles/1476278427.html
3. https://raspberrypi.stackexchange.com/questions/13358/insserv-warning-script-mathkernel-missing-lsb-tags-and-overrides
