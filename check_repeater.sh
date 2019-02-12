#!/bin/sh

while true
do
    totalNum=`ps cax | grep inq | wc -l`

    echo $totalNum
    if [ $totalNum -eq 0 ] ; then
        echo "inq is NOT running."
        /usr/local/bin/inq &
    else
        echo "inq is running."
    fi

    totalNumD=`ps cax | grep deq | wc -l`

    echo $totalNumD
    if [ $totalNumD -eq 0 ] ; then
        echo "deq is NOT running."
        /usr/local/bin/deq &
    else
        echo "deq is running."
    fi

    sleep 3
done
