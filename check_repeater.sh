#!/bin/sh

while true
do
    totalNum=`ps cax | grep inq | wc -l`

    echo $totalNum
    if [ $totalNum -eq 0 ] ; then
        echo "inq is NOT running."
        /mnt/data/LoRaRepeater/inq.py &
    else
        echo "inq is running."
    fi

    sleep 3

    totalNumD=`ps cax | grep deq | wc -l`

    echo $totalNumD
    if [ $totalNumD -eq 0 ] ; then
        echo "deq is NOT running."
        /mnt/data/LoRaRepeater/deq.py &
    else
        echo "deq is running."
    fi

    sleep 3

    file="repeater_upgrade.zip"
    cd /mnt/data/Ftpdir
    if [ -f "$file" ];then
        echo "Find upgrade FW"
        #killall check_repeater.sh
        killall inq.py deq.py
        unzip -o /mnt/data/Ftpdir/repeater_upgrade.zip -d /mnt/data/LoRaRepeater
        rm repeater_upgrade.zip

        #To setup starting daemon after booting
        cd /mnt/data/LoRaRepeater
        cp lora_repeater_starter /etc/init.d/
        chmod 755 /mnt/data/LoRaRepeater/inq.py /mnt/data/LoRaRepeater/deq.py /mnt/data/LoRaRepeater/check_repeater.sh /etc/init.d/lora_repeater_starter
        update-rc.d -f lora_repeater_starter remove;
        update-rc.d lora_repeater_starter defaults 99;

        reboot
    fi
done
