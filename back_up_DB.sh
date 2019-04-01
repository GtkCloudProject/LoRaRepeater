#!/bin/bash

echo "back up mysql sensor database sensordata table"
mysqldump -uroot -p123456 sensor sensordata > /mnt/data/Ftpdir/sensordata.sql
echo "back up done!"
