#!/bin/bash
TableName=$1
Count=$2
RANDOM=$$

max=Count
echo "Delete Multiple Data to DB"
echo "Count = $2"
if [ "$1" = "sensordata" ]
then
    echo "Delete sersordata Table"
    mysql -uroot -p123456 sensor -e "delete from sensordata order by time limit $2"
elif [ "$1" = "correctiontime" ]
then
    echo "Delete correctiontime Table"
    mysql -uroot -p123456 sensor -e "delete from correctiontime order by time limit $2"
elif [ "$1" = "retransmission" ]
then
    echo "Delete retransmission Table"
    mysql -uroot -p123456 sensor -e "delete from retransmission order by time limit $2"
fi
echo "Insert Delete!";