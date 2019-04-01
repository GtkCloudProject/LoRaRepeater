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
    #source /mnt/data/LoRaRepeater/install.sh
    reboot
    fi
done
