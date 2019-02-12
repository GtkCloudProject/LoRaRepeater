# lora_repeater

It's Lora Repeater suite runs on Python scriptes, includes:
1. inq.py under /usr/local/bin/ -- means received Mqtt payload from LoRa Gateway and put it to /var/lora_repeater/queue
2. deq.py under /usr/local/bin/ -- means repeat send queue's data by its LoRa Node module from /var/lora_repeater_sending -
   - if sent, the payload will be move to /var/lora_repeater/sent
   - if fail, the payload will be move to /var/lora_repeater/fail
   - all data log in /var/lora_repeater/log and its rotate by 10MB.
3. lora_repeater_stater, inq and deq service starter under /etc/init.d/


Installation step:
1. install required packages:
 - #sudo apt-get update
 - #sudo apt-get install -y mosquitto python-pip
 - #sudo pip install paho-mqtt python-etcd pyserial
 - #sudo pip install --user pymysql
 - #sudo pip install --user natsort
2. install lora_repeater package
 - #sudo su
 - #cd
 - #To get code by wget or tftp command from http server or tftp server (ex: your PC) and put these code to /root/lora_repeater/ of ODU
 - #cd lora_repeater
 - #cp inq.py deq.py /usr/local/bin/
 - #cp lora_repeater_starter /etc/init.d/
 - #chmod 755 /usr/local/bin/inq.py /usr/local/bin/deq.py /etc/init.d/lora_repeater_starter
 - #mv /usr/local/bin/inq.py /usr/local/bin/inq; mv /usr/local/bin/deq.py /usr/local/bin/deq
 - #update-rc.d lora_repeater_starter defaults
 - #chmod 777 lora_repeater_starter
 - #lora_repeater_starter start or reboot wil be run.

OR just 2 steps:
 1. #wget https://raw.githubusercontent.com/hc-liu/lora_repeater/master/setup.sh
 2. #chmod +x setup.sh ; ./setup.sh
 3. #cp check_repeater.sh /root
 4. #crontab -e
 5. add one line */1 * * * * /root/check_repeater.sh for each 1 min to check deq/ine processes

References:
1. https://stackoverflow.com/questions/7266558/pyserial-buffer-wont-flush
2. http://www.itread01.com/articles/1476278427.html
3. https://raspberrypi.stackexchange.com/questions/13358/insserv-warning-script-mathkernel-missing-lsb-tags-and-overrides
