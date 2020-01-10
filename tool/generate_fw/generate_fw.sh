#! /bin/sh

rm -rf default
rm -rf 0500*
git clone https://github.com/GtkCloudProject/LoRaRepeater.git
cat LoRaRepeater/VERSION

mkdir default
cp -rf LoRaRepeater ./default/
cd ./default/LoRaRepeater/
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001001
cp -rf LoRaRepeater ./05001001/
cd ./05001001/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001001.sh
echo "To chage the IP of 05001001 FW"
sh ./ch_ip_05001001.sh
git checkout ./ch_ip_05001001.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""


mkdir 05001001SF12
cp -rf LoRaRepeater ./05001001SF12/
cd ./05001001SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001001.sh
echo "To chage the IP of 05001001 FW"
sh ./ch_ip_05001001.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001001.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""


mkdir 05001002
cp -rf LoRaRepeater ./05001002/
cd ./05001002/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001002.sh
echo "To chage the IP of 05001002 FW"
sh ./ch_ip_05001002.sh
git checkout ./ch_ip_05001002.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""


mkdir 05001002SF12
cp -rf LoRaRepeater ./05001002SF12/
cd ./05001002SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001002.sh
echo "To chage the IP of 05001002 FW"
sh ./ch_ip_05001002.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001002.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001003
cp -rf LoRaRepeater ./05001003/
cd ./05001003/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001003.sh
echo "To chage the IP of 05001003 FW"
sh ./ch_ip_05001003.sh
git checkout ./ch_ip_05001003.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001003SF12
cp -rf LoRaRepeater ./05001003SF12/
cd ./05001003SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001003.sh
echo "To chage the IP of 05001003 FW"
sh ./ch_ip_05001003.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001003.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""


mkdir 05001004
cp -rf LoRaRepeater ./05001004/
cd ./05001004/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001004.sh
echo "To chage the IP of 05001004 FW"
sh ./ch_ip_05001004.sh
git checkout ./ch_ip_05001004.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001004SF12
cp -rf LoRaRepeater ./05001004SF12/
cd ./05001004SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001004.sh
echo "To chage the IP of 05001004 FW"
sh ./ch_ip_05001004.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001004.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001005
cp -rf LoRaRepeater ./05001005/
cd ./05001005/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001005.sh
echo "To chage the IP of 05001005 FW"
sh ./ch_ip_05001005.sh
git checkout ./ch_ip_05001005.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001005SF12
cp -rf LoRaRepeater ./05001005SF12/
cd ./05001005SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001005.sh
echo "To chage the IP of 05001005 FW"
sh ./ch_ip_05001005.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001005.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001006
cp -rf LoRaRepeater ./05001006/
cd ./05001006/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001006.sh
echo "To chage the IP of 05001006 FW"
sh ./ch_ip_05001006.sh
git checkout ./ch_ip_05001006.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001006SF12
cp -rf LoRaRepeater ./05001006SF12/
cd ./05001006SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001006.sh
echo "To chage the IP of 05001006 FW"
sh ./ch_ip_05001006.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001006.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001007
cp -rf LoRaRepeater ./05001007/
cd ./05001007/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001007.sh
echo "To chage the IP of 05001007 FW"
sh ./ch_ip_05001007.sh
git checkout ./ch_ip_05001007.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001007SF12
cp -rf LoRaRepeater ./05001007SF12/
cd ./05001007SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001007.sh
echo "To chage the IP of 05001007 FW"
sh ./ch_ip_05001007.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001007.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001008
cp -rf LoRaRepeater ./05001008/
cd ./05001008/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001008.sh
echo "To chage the IP of 05001008 FW"
sh ./ch_ip_05001008.sh
git checkout ./ch_ip_05001008.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001008SF12
cp -rf LoRaRepeater ./05001008SF12/
cd ./05001008SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001008.sh
echo "To chage the IP of 05001008 FW"
sh ./ch_ip_05001008.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001008.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001009
cp -rf LoRaRepeater ./05001009/
cd ./05001009/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001009.sh
echo "To chage the IP of 05001009 FW"
sh ./ch_ip_05001009.sh
git checkout ./ch_ip_05001009.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05001009SF12
cp -rf LoRaRepeater ./05001009SF12/
cd ./05001009SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05001009.sh
echo "To chage the IP of 05001009 FW"
sh ./ch_ip_05001009.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05001009.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 0500100a
cp -rf LoRaRepeater ./0500100a/
cd ./0500100a/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_0500100a.sh
echo "To chage the IP of 0500100a FW"
sh ./ch_ip_0500100a.sh
git checkout ./ch_ip_0500100a.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 0500100aSF12
cp -rf LoRaRepeater ./0500100aSF12/
cd ./0500100aSF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_0500100a.sh
echo "To chage the IP of 0500100a FW"
sh ./ch_ip_0500100a.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_0500100a.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002001
cp -rf LoRaRepeater ./05002001/
cd ./05002001/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002001.sh
echo "To chage the IP of 05002001 FW"
sh ./ch_ip_05002001.sh
git checkout ./ch_ip_05002001.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002001SF12
cp -rf LoRaRepeater ./05002001SF12/
cd ./05002001SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002001.sh
echo "To chage the IP of 05002001 FW"
sh ./ch_ip_05002001.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05002001.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002002
cp -rf LoRaRepeater ./05002002/
cd ./05002002/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002002.sh
echo "To chage the IP of 05002002 FW"
sh ./ch_ip_05002002.sh
git checkout ./ch_ip_05002002.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002002SF12
cp -rf LoRaRepeater ./05002002SF12/
cd ./05002002SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002002.sh
echo "To chage the IP of 05002002 FW"
sh ./ch_ip_05002002.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05002002.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002003
cp -rf LoRaRepeater ./05002003/
cd ./05002003/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002003.sh
echo "To chage the IP of 05002003 FW"
sh ./ch_ip_05002003.sh
git checkout ./ch_ip_05002003.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002003SF12
cp -rf LoRaRepeater ./05002003SF12/
cd ./05002003SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002003.sh
echo "To chage the IP of 05002003 FW"
sh ./ch_ip_05002003.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05002003.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002004
cp -rf LoRaRepeater ./05002004/
cd ./05002004/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002004.sh
echo "To chage the IP of 05002004 FW"
sh ./ch_ip_05002004.sh
git checkout ./ch_ip_05002004.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002004SF12
cp -rf LoRaRepeater ./05002004SF12/
cd ./05002004SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002004.sh
echo "To chage the IP of 05002004 FW"
sh ./ch_ip_05002004.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05002004.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002005
cp -rf LoRaRepeater ./05002005/
cd ./05002005/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002005.sh
echo "To chage the IP of 05002005 FW"
sh ./ch_ip_05002005.sh
git checkout ./ch_ip_05002005.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002005SF12
cp -rf LoRaRepeater ./05002005SF12/
cd ./05002005SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002005.sh
echo "To chage the IP of 05002005 FW"
sh ./ch_ip_05002005.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05002005.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002006
cp -rf LoRaRepeater ./05002006/
cd ./05002006/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002006.sh
echo "To chage the IP of 05002006 FW"
sh ./ch_ip_05002006.sh
git checkout ./ch_ip_05002006.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05002006SF12
cp -rf LoRaRepeater ./05002006SF12/
cd ./05002006SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05002006.sh
echo "To chage the IP of 05002006 FW"
sh ./ch_ip_05002006.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05002006.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05003001
cp -rf LoRaRepeater ./05003001/
cd ./05003001/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05003001.sh
echo "To chage the IP of 05003001 FW"
sh ./ch_ip_05003001.sh
git checkout ./ch_ip_05003001.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05003001SF12
cp -rf LoRaRepeater ./05003001SF12/
cd ./05003001SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05003001.sh
echo "To chage the IP of 05003001 FW"
sh ./ch_ip_05003001.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05003001.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05003002
cp -rf LoRaRepeater ./05003002/
cd ./05003002/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05003002.sh
echo "To chage the IP of 05003002 FW"
sh ./ch_ip_05003002.sh
git checkout ./ch_ip_05003002.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05003002SF12
cp -rf LoRaRepeater ./05003002SF12/
cd ./05003002SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05003002.sh
echo "To chage the IP of 05003002 FW"
sh ./ch_ip_05003002.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05003002.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05004001
cp -rf LoRaRepeater ./05004001/
cd ./05004001/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05004001.sh
echo "To chage the IP of 05004001 FW"
sh ./ch_ip_05004001.sh
git checkout ./ch_ip_05004001.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

mkdir 05004001SF12
cp -rf LoRaRepeater ./05004001SF12/
cd ./05004001SF12/LoRaRepeater/tool/change_ip/
sed -i 's/\/mnt\/data\/LoRaRepeater/\.\.\/\.\./g' ./ch_ip_05004001.sh
echo "To chage the IP of 05004001 FW"
sh ./ch_ip_05004001.sh
sed -i 's/SF_VALUE=10/SF_VALUE=12/g' ../../deq.py
git checkout ./ch_ip_05004001.sh
cd ../../
rm -rf .git
zip -r repeater_upgrade ./*
mv repeater_upgrade.zip ../
cd ../
rm -rf LoRaRepeater
cd ../
echo ""

rm -rf LoRaRepeater
