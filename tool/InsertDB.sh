#!/bin/bash
TableName=$1
Count=$2
RANDOM=$$
max=Count

echo "Insert Multiple Data to DB"

if [ "$1" = "sensordata" ]
then
    echo "Insert sersordata Table"
    mysql -uroot -p123456 sensor -e"create table if not exists sensordata(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, retransmit_flag BOOLEAN NOT NULL default 0, frame_count CHAR(8) NOT NULL, UNIQUE(source_mac_address, time, frame_count))"
    for ((i=1; i<=max; i=i+1))
    do
        mysql -uroot -p123456 sensor -e "insert ignore into $1 (source_mac_address, time, raw_data, frame_count) values('05$(($RANDOM+100000))', FROM_UNIXTIME(UNIX_TIMESTAMP('2010-04-30 14:53:27') + FLOOR(0 + (RAND() * 63072000))), '2$(($RANDOM*35+1000000))$(($RANDOM+10000000))', '$(($RANDOM+100000))')"
    done
elif [ "$1" = "correctiontime" ]
then
    echo "Insert correctiontime Table"
    mysql -uroot -p123456 sensor -e"create table if not exists correctiontime(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, frame_count CHAR(8) NOT NULL, UNIQUE(source_mac_address, time, frame_count))"
    for ((i=1; i<=max; i=i+1))
    do
        mysql -uroot -p123456 sensor -e "insert ignore into $1 (source_mac_address, time, raw_data, frame_count) values('05$(($RANDOM+100000))', FROM_UNIXTIME(UNIX_TIMESTAMP('2010-04-30 14:53:27') + FLOOR(0 + (RAND() * 63072000))), '4$(($RANDOM*35+1000000))$(($RANDOM+10000000))', '$(($RANDOM+100000))')"
    done
elif [ "$1" = "retransmission" ]
then
    echo "Insert retransmission Table"
    mysql -uroot -p123456 sensor -e"create table if not exists retransmission(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, frame_count CHAR(8) NOT NULL,UNIQUE(source_mac_address, time))"
    for ((i=1; i<=max; i=i+1))
    do
        mysql -uroot -p123456 sensor -e "insert ignore into $1 (source_mac_address, time, raw_data, frame_count) values('05$(($RANDOM+100000))', FROM_UNIXTIME(UNIX_TIMESTAMP('2010-04-30 14:53:27') + FLOOR(0 + (RAND() * 63072000))), '8$(($RANDOM*35+1000000))$(($RANDOM+10000000))', '$(($RANDOM+100000))')"
    done
fi
echo "Insert Finished!";