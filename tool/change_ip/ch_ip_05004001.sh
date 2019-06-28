#!/bin/sh

App_Server_IP="10.56.149.102"
Diag_PC_IP="10.56.149.202"
NPort_IP="10.56.149.203"

#To change the IP of inq.py
sed -i 's/10.56.147.176/'$App_Server_IP'/g' /mnt/data/LoRaRepeater/inq.py
sed -i 's/10.56.147.240/'$Diag_PC_IP'/g' /mnt/data/LoRaRepeater/inq.py
sed -i 's/10.56.147.241/'$NPort_IP'/g' /mnt/data/LoRaRepeater/inq.py

#To change the IP of deq.py
sed -i 's/10.56.147.176/'$App_Server_IP'/g' /mnt/data/LoRaRepeater/deq.py
sed -i 's/10.56.147.240/'$Diag_PC_IP'/g' /mnt/data/LoRaRepeater/deq.py
sed -i 's/10.56.147.241/'$NPort_IP'/g' /mnt/data/LoRaRepeater/deq.py

echo "The IP Setting is successful, as following:"
echo "  - Application SERVER IP : $App_Server_IP"
echo "  - Diagnosis PC IP : $Diag_PC_IP"
echo "  - NPort 5450 IP : $NPort_IP"
