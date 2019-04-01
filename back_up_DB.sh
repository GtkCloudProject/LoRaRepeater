#!/bin/bash

echo "back up mysql sensor database sensordata table"
mysqldump -uroot -p123456 sensor sensordata > /mnt/data/Ftpdir/sensordata.sql
cd /mnt/data/Ftpdir
zip sensordata.zip sensordata.sql
rm sensordata.sql
echo "back up done!"
