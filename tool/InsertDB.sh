#!/bin/bash
TableName=$1
Count=$2
RANDOM=$$

max=Count
echo "Insert Multiple Data to DB"

if [ "$1" = "sensordata" ]
then
    echo "Insert sersordata Table"
    for ((i=1; i<=max; i=i+1))
    do
        mysql -uroot -p123456 sensor -e "insert ignore into $1 (source_mac_address, time, raw_data, frame_count) values('$RANDOM', FROM_UNIXTIME(UNIX_TIMESTAMP('2010-04-30 14:53:27') + FLOOR(0 + (RAND() * 63072000))), RAND()*46786401, RAND()*86401)"
    done
elif [ "$1" = "correctiontime" ]
then
    echo "Insert correctiontime Table"
    for ((i=1; i<=max; i=i+1))
    do
        mysql -uroot -p123456 sensor -e "insert ignore into $1 (source_mac_address, time, raw_data, frame_count) values('$RANDOM', FROM_UNIXTIME(UNIX_TIMESTAMP('2010-04-30 14:53:27') + FLOOR(0 + (RAND() * 63072000))), RAND()*46786401, RAND()*86401)"
    done
elif [ "$1" = "retransmission" ]
then
    echo "Insert retransmission Table"
    for ((i=1; i<=max; i=i+1))
    do
        mysql -uroot -p123456 sensor -e "insert ignore into $1 (source_mac_address, time, raw_data, frame_count) values('$RANDOM', FROM_UNIXTIME(UNIX_TIMESTAMP('2010-04-30 14:53:27') + FLOOR(0 + (RAND() * 63072000))), RAND()*46786401, RAND()*86401)"
    done
fi
echo "Insert Finished!";