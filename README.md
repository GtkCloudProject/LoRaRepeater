# lora_repeater

It's Lora Repeater suite runs on Python scriptes, includes:
 1. inq.py under /mnt/data/LoRaRepeater/ -- a. received Mqtt payload from LoRa Gateway and forward it to another repeater.
                                            b. received sensor data then put it to the database.
                                            c. received correction time command and replace system tinme.
                                            d. received retransmission command and select witch sensor data need to be sent.
 2. deq.py under /mnt/data/LoRaRepeater/ -- a. forward sensor's data withch store in database and send that by LoRa module.
                                            b. forward sensor's data, correction time ack and retransmission ack data to application server by ethernet socket.
                                            c. forward correction time command
                                            d. forward retransmission command
 3. all data log in /mnt/data/Ftpdir/ and its rotate by 20MB.
 4. lora_repeater_stater, inq and deq service starter under /etc/init.d/

Installation LoRa Repeater FW steps:(Never installed)
 1. sudo su
 2. apt-get update
 3. apt-get install -y git
 4. cd /mnt/data/
 5. git clone https://github.com/GtkCloudProject/LoRaRepeater.git
 6. cd /mnt/data/LoRaRepeater
 7. sh /mnt/data/LoRaRepeater/install.sh
 8. reboot

Update LoRa Repeater FW (already install LoRa Repeater FW)
 1. sudo su
 2. cd /mnt/data/LoRaRepeater
 3. killall check_repeater.sh ; killall inq.py deq.py
 4. git checkout *
 5. git pull --rebase
 6. source /mnt/data/LoRaRepeater/install.sh
 7. reboot

References:
 1. https://stackoverflow.com/questions/7266558/pyserial-buffer-wont-flush
 2. http://www.itread01.com/articles/1476278427.html
 3. https://raspberrypi.stackexchange.com/questions/13358/insserv-warning-script-mathkernel-missing-lsb-tags-and-overrides
