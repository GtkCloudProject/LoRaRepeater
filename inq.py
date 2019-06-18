#!/usr/bin/python

"""
@file inq.py
@brief 1. received Mqtt payload from LoRa Gateway and forward it to another repeater.
       2. received sensor data then put it to the database.
       3. received correction time command and replace system tinme.
       4. received retransmission command and select witch sensor data need to be sent.
@author Nick Lee / Chris Chang
@date 2019/06
"""

#System Imports
import paho.mqtt.client as mqtt
import threading
import json
import sys
import os
import logging
import pymysql.cursors
import socket,select
import serial
import time
import struct
import binascii
from logging.handlers import RotatingFileHandler

USB_DEV_ARRAY = ["/dev/ttyS0"]

LORA_VERIFY_STR = "3132333435363738393061"
MY_LOG_FILE_PATH = "/mnt/data/Ftpdir/"
MY_LOG_FILENAME = MY_LOG_FILE_PATH + "inq.log"
REPLY_STRING = "+CDEVADDR:"
my_dict = {}


NETSTAT_NPORT1_IP = "10.56.147.241"
NETSTAT_NPORT1_PORT = "4001"
NETSTAT_NPORT2_IP = "10.56.147.241"
NETSTAT_NPORT2_PORT = "4002"
NETSTAT_APPLICATION_IP = "10.56.147.176"
NETSTAT_APPLICATION_PORT = "4006"

Nport1_ip_port = ('10.56.147.241',4001) #water meter
Nport2_ip_port = ('10.56.147.241',4002) #rain meter
Nport3_ip_port = ('10.56.147.241',4003) #radio
Nport4_ip_port = ('10.56.147.241',4004) #display
Diagnosis_PC_ip_port = ('10.56.147.240',4005)
Application_Server_ip_port = ('10.56.147.176',4006)

MAC_Address=0
Self_MAC_Level=0
Sensor_Count=0
Endian = '>' #big-endian
MAX_DB_Count = 99999

#select socket queue
g_socket_list = []

#socket flag
g_sock1_flag = -1
g_sock2_flag = -1
g_sock3_flag = -1

#select timeout
SELECT_TIMEOUT = 1

#mutex lock for accessing DB
g_db_mutex = threading.Lock()

#socket UNKNOW status
SOCK_UNKNOW = "unkn"

# Set up a specific logger with our desired output level
my_logger = logging.getLogger('enqueue')
# Add the log message handler to the logger
my_logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(MY_LOG_FILENAME, maxBytes=2048000, backupCount=10)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
my_logger.addHandler(handler)
my_logger.info("inq.py started!!!")
# example
# my_logger.debug('debug message')
# my_logger.info('info message')
# my_logger.warn('warn message')
# my_logger.error('error message')
# my_logger.critical('critical message')

"""
To close socket
"""
def close_socket(sock_c):
    global g_socket_list

    sock_c.close()
    try:
        g_socket_list.remove(sock_c)
    except ValueError:
        pass

"""
Obtain MAC Address from serial interface by at command
"""
def get_lora_module_addr(dev_path):
    try:
        ser = serial.Serial(dev_path, 9600, timeout=0.5)
        ser.flushInput()
        ser.flushOutput()
        ser.write("AT+cdevaddr?\r\n")
        check_my_dongle = str(ser.readlines())
        # my_logger.info("check_my_dongle")
        global MAC_Address, Self_MAC_Level
        MAC_Address = check_my_dongle[check_my_dongle.find(REPLY_STRING) + 10: check_my_dongle.find(REPLY_STRING) + 18]
        my_logger.info("MAC_Address:"+str(MAC_Address))
        if(MAC_Address[4:5]=='1'):
            Self_MAC_Level = 1
        elif (MAC_Address[4:5]=='2'):
            Self_MAC_Level = 2
        elif (MAC_Address[4:5]=='3'):
            Self_MAC_Level = 3
        elif (MAC_Address[4:5]=='4'):
            Self_MAC_Level = 4
        else:
            Self_MAC_Level = 0
            my_logger.info("MAC Level Error reset to 0")
        #my_logger.info("My USB dongle checked")
        return ser
        #else:
            #return None
    except serial.serialutil.SerialException:
        #  my_logger.info("FAIL: Cannot open Serial Port (No LoRa Node Inserted)")
        return None

"""
Create three database tables(sensordata, correctiontime, retransmission), if not exist, will create new one.
"""
def Create_DB():
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 #db='lora',
                                 #charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    #if self is source sensor, write into DB else store forward data
    try:
        with connection.cursor() as cursor:
            # Read a single record
            # sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
            my_logger.info("connect to DB")
            sql = "create database if not exists sensor"
            cursor.execute(sql)
            cursor.execute("USE sensor")
            my_logger.info("create sensordata table to DB")
            sql = "create table if not exists sensordata(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, retransmit_flag BOOLEAN NOT NULL default 0, frame_count INT NOT NULL, last_sent_time timestamp NOT NULL, UNIQUE(source_mac_address, time, frame_count))"
            cursor.execute(sql)
            my_logger.info("create correctiontime table to DB")
            sql = "create table if not exists correctiontime(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, frame_count INT NOT NULL, last_sent_time timestamp NOT NULL, UNIQUE(source_mac_address, time))"
            cursor.execute(sql)
            my_logger.info("create retransmission table to DB")
            sql = "create table if not exists retransmission(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, frame_count INT NOT NULL, last_sent_time timestamp NOT NULL, UNIQUE(source_mac_address, time, frame_count))"
            cursor.execute(sql)
    finally:
        my_logger.info("connection close!")

"""
Connect to database and put the sensor data to database tables, db_type 1:Water 2:Rain 3:Lora 4:correctiontime 5:retransmission
"""
def connect_DB_put_data(db_type, p_sensor_mac, p_sensor_data, p_sensor_count): #db_type 1:Water 2:Rain 3:Lora 4:correctiontime 5:retransmission

    global g_db_mutex, Sensor_Count

    if g_db_mutex.acquire():
        # Connect to the database
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='123456',
                                     #db='lora',
                                     #charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        #if self is source sensor, write into DB else store forward data
        try:
            with connection.cursor() as cursor:
                # Read a single record
                # sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
                my_logger.info("connect to DB")
                cursor.execute("USE sensor")
                my_logger.info ("p_sensor_mac:"+str(p_sensor_mac))
                SourceMACAddress = MAC_Address
                if db_type == 1: # parameter = Water
                    my_logger.info("parameter = Water")
                    sql = "select count(*) from sensordata"
                    cursor.execute(sql)
                    for row in cursor:
                        number_of_rows = row["count(*)"]
                    my_logger.info("number_of_rows is:"+str(number_of_rows))
                    # delete data if reach to MAX DB counter 99999
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        my_logger.info("Delete number_of_rows is:"+str(del_number))
                        sql = "delete from sensordata order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    # insert to DB
                    sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', %s)" % (SourceMACAddress, time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                    cursor.execute(sql)
                    connection.commit()
                elif db_type == 2: #parameter = Rain
                    my_logger.info("parameter = Rain")
                    sql = "select count(*) from sensordata"
                    cursor.execute(sql)
                    for row in cursor:
                        number_of_rows = row["count(*)"]
                    my_logger.info("number_of_rows is:"+str(number_of_rows))
                    # delete data if reach to MAX DB counter 99999
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        my_logger.info("Delete number_of_rows is:"+str(del_number))
                        sql = "delete from sensordata order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    # insert to DB
                    sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', %s)" % (SourceMACAddress, time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                    cursor.execute(sql)
                    connection.commit()
                elif db_type == 3: # parameter = Lora
                    my_logger.info("parameter = Lora")
                    sql = "select count(*) from sensordata"
                    cursor.execute(sql)
                    for row in cursor:
                        number_of_rows = row["count(*)"]
                    my_logger.info("number_of_rows is:"+str(number_of_rows))
                    # delete data if reach to MAX DB counter 99999
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        my_logger.info("Delete number_of_rows is:"+str(del_number))
                        sql = "delete from sensordata order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    # insert to DB
                    sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', '%s')" % (p_sensor_mac,time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                    cursor.execute(sql)
                    connection.commit()
                elif db_type == 4: # parameter = Correction Time
                    my_logger.info("parameter = Correction Time")
                    sql = "select count(*) from correctiontime"
                    cursor.execute(sql)
                    for row in cursor:
                        number_of_rows = row["count(*)"]
                    my_logger.info("number_of_rows is:"+str(number_of_rows))
                    # delete data if reach to MAX DB counter 99999
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        my_logger.info("Delete number_of_rows is:"+str(del_number))
                        sql = "delete from correctiontime order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    # select from DB, check this correction command is not at cool down 2 minutes
                    sql = "select sended_flag, raw_data, source_mac_address, frame_count, last_sent_time from correctiontime WHERE last_sent_time > DATE_SUB(now(), INTERVAL 2 MINUTE) and last_sent_time < now() and source_mac_address='%s'" % (p_sensor_mac)
                    cursor.execute(sql)
                    my_logger.info("cursor.rowcount:"+str(cursor.rowcount))
                    # rowcount = 0, means not at cool down 2 minutes
                    if(cursor.rowcount==0):
                        sql = "insert ignore into correctiontime (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', '%s') ON DUPLICATE KEY UPDATE sended_flag =0, last_sent_time=now()" % (p_sensor_mac,time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                        cursor.execute(sql)
                        connection.commit()
                        # if reveive broadcast packet, replace system time
                        if 'ffffff' in p_sensor_mac or 'FFFFFF' in p_sensor_mac:
                            #replace system time here by nick
                            my_logger.info("Replace system time!!!")
                            strtime = time.strftime('%Y-%m-%d %H:%M:%S',tmp_time)
                            my_logger.info("strtime:"+str(strtime))
                            os.system('date -s "%s"' % strtime)
                    else:
                        my_logger.info("Replace system time, wait colddown 2 mins")
                elif db_type == 5: # parameter = Retransmition
                    my_logger.info("parameter = Retransmition")
                    sql = "select count(*) from retransmission"
                    cursor.execute(sql)
                    for row in cursor:
                        number_of_rows = row["count(*)"]
                    my_logger.info("number_of_rows is:"+str(number_of_rows))
                    # delete data if reach to MAX DB counter 99999
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        my_logger.info("Delete number_of_rows is:"+str(del_number))
                        sql = "delete from retransmission order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    time_interval = int(p_sensor_data[10:12],16)
                    my_logger.info("time_interval:"+str(time_interval))
                    # select from DB, check this Retransmition command is not at cool down 2 minutes
                    sql = "select sended_flag, raw_data, source_mac_address, frame_count, last_sent_time from retransmission WHERE last_sent_time > DATE_SUB(now(), INTERVAL 2 MINUTE) and source_mac_address='%s' and time='%s'" % (p_sensor_mac, time.strftime('%Y-%m-%d %H:%M:%S',tmp_time))
                    cursor.execute(sql)
                    my_logger.info("cursor.rowcount:"+str(cursor.rowcount))
                    # rowcount = 0, means not at cool down 2 minutes
                    if(cursor.rowcount==0):
                        sql = "insert ignore into retransmission(source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', '%s') ON DUPLICATE KEY UPDATE sended_flag =0, last_sent_time=now()" % (p_sensor_mac,time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                        cursor.execute(sql)
                        connection.commit()
                    else:
                        my_logger.info("update sended_flag fail, wait colddown 2 mins")
        finally:
            my_logger.info("connection close!")
            connection.close()
        g_db_mutex.release()

"""
Connect to database and select which sensordata should beretransmit db_type 1: select data to retransmit 2: if doesn't exist select data then insert new retransmit data
"""
def connect_DB_select_data(db_type, sensor_mac, time, time_interval, sensor_data, sensor_count): #db_type 1: select data to retransmit 2: if doesn't exist select data then insert new retransmit data
    global Sensor_Count
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 #db='lora',
                                 #charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    #if self is source sensor, write into DB else store forward data
    try:
        with connection.cursor() as cursor:
            # Read a single record
            # sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
            my_logger.info("connect to DB select data")
            cursor.execute("USE sensor")
            my_logger.info("sensor_mac:"+str(sensor_mac))
            # select from DB, check this select retransmit data command is not at cool down 2 minutes
            if db_type == 1:
                sql = "select sended_flag, retransmit_flag, raw_data, source_mac_address, frame_count, last_sent_time from sensordata WHERE last_sent_time > DATE_SUB(now(), INTERVAL 2 MINUTE) and retransmit_flag =1"
                cursor.execute(sql)
                my_logger.info("cursor.rowcount:"+str(cursor.rowcount))
                # rowcount = 0, means not at cool down 2 minutes
                if(cursor.rowcount==0):
                    sql = "select source_mac_address, sended_flag, retransmit_flag, raw_data, frame_count from sensordata WHERE time >='%s' and time < DATE_ADD('%s', INTERVAL '%s' MINUTE) and source_mac_address='%s'" % (time, time, time_interval, sensor_mac)
                    cursor.execute(sql)
                    my_logger.info("cursor.rowcount:"+str(cursor.rowcount))
                    if(cursor.rowcount>0):
                        for index in range(cursor.rowcount):
                            my_logger.info("index:"+str(index))
                            if Sensor_Count == 9999:
                                Sensor_Count = 1
                            else:
                                Sensor_Count +=1
                            my_logger.info("Sensor count:"+str(Sensor_Count))
                            sql = "UPDATE sensordata SET retransmit_flag =1, frame_count='%s', last_sent_time=now() where time >='%s' and time < DATE_ADD('%s', INTERVAL '%s' MINUTE) and source_mac_address='%s' and retransmit_flag =0 limit 1" % (Sensor_Count, time, time, time_interval, sensor_mac)
                            cursor.execute(sql)
                            connection.commit()
                else:
                    my_logger.info("select retransmit data, update retransmit_flag fail, wait colddown 2 mins")
            elif db_type == 2:
                sql = "select count(*) from sensordata"
                cursor.execute(sql)
                for row in cursor:
                   number_of_rows = row["count(*)"]
                my_logger.info("number_of_rows is:"+str(number_of_rows))
                # delete data if reach to MAX DB counter 99999
                if number_of_rows > MAX_DB_Count:
                    del_number = number_of_rows - MAX_DB_Count
                    my_logger.info("Delete number_of_rows is:"+str(del_number))
                    sql = "delete from sensordata order by time limit %s" % del_number
                    cursor.execute(sql)
                    connection.commit()
                # select from DB, check this select retransmit ACK data command is not at cool down 2 minutes
                sql = "select sended_flag, retransmit_flag, raw_data, source_mac_address, frame_count, last_sent_time from sensordata WHERE last_sent_time > DATE_SUB(now(), INTERVAL 2 MINUTE) and source_mac_address='%s' and frame_count='%s'" % (sensor_mac, sensor_count)
                cursor.execute(sql)
                # rowcount = 0, means not at cool down 2 minutes
                if(cursor.rowcount==0):
                    sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count, sended_flag, retransmit_flag) values('%s', '%s', '%s', '%s', 1, 1) ON DUPLICATE KEY UPDATE retransmit_flag =1, last_sent_time=now()" % (sensor_mac, time, sensor_data, sensor_count)
                    cursor.execute(sql)
                    connection.commit()
                else:
                    my_logger.info("select retransmit ACK data, update retransmit_flag fail, wait colddown 2 mins")
    finally:
        my_logger.info("connection close!")
        connection.close()

"""
The callback for when the client receives a CONNACK response from the mqtt server.
"""
def on_connect(client, userdata, flags, rc):
    my_logger.info("Mqtt Connected.")
    client.subscribe("#")

"""
The callback for when a PUBLISH message is received from the mqtt server.
"""
def on_message(client, userdata, msg):
    global Sensor_Count
    json_count1 = 0
    try:
        json_data = msg.payload
        json_array_size = len(json.loads(json_data))
        while json_count1 < json_array_size:
            sensor_mac = json.loads(json_data)[json_count1]['macAddr']
            sensor_data = json.loads(json_data)[json_count1]['data']
            sensor_count = json.loads(json_data)[json_count1]['frameCnt']
            nFrameCnt = json.loads(json_data)[json_count1]['frameCnt']
            my_logger.info("Receive Lora Data is:"+str(sensor_data))
            Data_Len = len(sensor_data)
            my_logger.info("Data_Len is:"+str(Data_Len))
            my_logger.info("sensor_count is:"+str(sensor_count))
            Command = int(sensor_data[0:2],16)
            recv_mac_level = Command>>5
            CMD = (Command>>2) & ~( 1<<3 | 1<<4 | 1<<5)
            Data_type = Command & ~( 1<<2 | 1<<3 | 1<<4 | 1<<5 | 1<<6 | 1<<7 )
            # Store data to DB
            # Check the command if not sensor data do not insert to DB
            # Sensor Lora Packet
            if CMD == 0 and (Data_type == 1 or Data_type == 2):
                my_logger.info("Receive Sensor data from lora")
                # Forward L1->L2->L3->L4
                if Self_MAC_Level >= recv_mac_level:
                    my_logger.info("Ready to put sensor data to DB")
                    connect_DB_put_data(3, sensor_mac[8:16], sensor_data, sensor_count)
            # Correction Lora Packet
            elif Data_type == 0 and CMD == 1:
                my_logger.info("Receive Correction Lora Packet")
                my_logger.info("MAC_Address:"+str(MAC_Address))
                my_logger.info("sensor_mac[8:16]:"+str(sensor_mac[8:16]))
                # FFFFFF is Broadcast Correction Packet
                if 'ffffff' in sensor_mac[8:16] or 'FFFFFF' in sensor_mac[8:16]:
                    my_logger.info("Receive Broadcast Correction Packet")
                    #pepare correction time ack
                    # Receive command L4->L3->L2->L1
                    if Self_MAC_Level <= recv_mac_level:
                        my_logger.info("Ready to put correction time data to DB")
                        connect_DB_put_data(4, sensor_mac[8:16], sensor_data, sensor_count) #forward broadcast correction time
                        if Sensor_Count == 9999:
                            Sensor_Count = 1
                        else:
                            Sensor_Count +=1
                        my_logger.info("Sensor count:"+str(Sensor_Count))
                        connect_DB_put_data(4, MAC_Address, sensor_data, Sensor_Count) #send ack correction
                else:
                    # Forward L1->L2->L3->L4
                    if Self_MAC_Level >= recv_mac_level:
                        my_logger.info("Forward Correction 'ACK' Packet")
                        connect_DB_put_data(4, sensor_mac[8:16], sensor_data, sensor_count)#forward ack correction
            # Retransmit Lora Packet
            elif (Data_type == 1 or Data_type == 2) and CMD == 2 and Data_Len == 20:
                my_logger.info("Receive Retransmit Lora Packet")
                #select witch sensor data need to retransmit
                retransmit_time = sensor_data[2:10]
                tmp_time = time.localtime(int(retransmit_time,16))
                strtime = time.strftime('%Y-%m-%d %H:%M:%S',tmp_time)
                my_logger.info("strtime:"+str(strtime))
                time_interval = int(sensor_data[10:12],16)
                my_logger.info("time_interval:"+str(time_interval))
                # Receive command L4->L3->L2->L1
                if Self_MAC_Level <= recv_mac_level:
                    my_logger.info("Ready to put retransmit data to DB")
                    connect_DB_put_data(5, sensor_mac[8:16], sensor_data, sensor_count)
                if sensor_data[12:20] == MAC_Address:
                    my_logger.info("Select Re-transmit data from DB")
                    connect_DB_select_data(1, sensor_data[12:20], strtime, time_interval, sensor_data , sensor_count)
            elif (Data_type == 1 or Data_type == 2) and CMD == 2 and Data_Len == 18:
                my_logger.info("Receive Retransmit ACK data from lora")
                # RForward L1->L2->L3->L4
                if Self_MAC_Level > recv_mac_level:
                    my_logger.info("Ready to put Retransmit sensor data to DB")
                    #select witch sensor data need to retransmit
                    retransmit_time = sensor_data[2:10]
                    tmp_time = time.localtime(int(retransmit_time,16))
                    strtime = time.strftime('%Y-%m-%d %H:%M:%S',tmp_time)
                    my_logger.info("strtime:"+str(strtime))
                    time_interval = 0
                    my_logger.info("time_interval:"+str(time_interval))
                    connect_DB_select_data(2, sensor_mac[8:16], strtime, time_interval, sensor_data , sensor_count)
            else:
                my_logger.info("not sensor data lora packet")
                if sensor_data == LORA_VERIFY_STR:
                    os.system("echo \"0\" > /tmp/lora_status")
                    os.system("sync")
            json_count1 = json_count1 + 1

    except:
        my_logger.info("Received a non-UTF8 msg")

"""
Check socket status, sock1: Water Meter, sock2: Rain Meter, sock3: application Server
"""
def TCP_connect(name):
    global sock1
    global sock2
    global sock3
    global g_sock1_flag
    global g_sock2_flag
    global g_sock3_flag
    global g_socket_list

    # Water Meter
    if name == Nport1_ip_port:
        try:
            sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock1.settimeout(1)
            sock1.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock1.connect(Nport1_ip_port)
            my_logger.info ("sock1 Water Meter connect")
            g_sock1_flag = 0
            g_socket_list.append(sock1)
            os.system("echo \"0\" > /tmp/Nport1_status")
            os.system("sync")
        except:
            my_logger.info("sock1 Water Meter connect error")
            g_sock1_flag = -1
            close_socket(sock1)
            os.system("echo \"-1\" > /tmp/Nport1_status")
            os.system("sync")
            pass

    # Rain Meter
    elif name == Nport2_ip_port:
        try:
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock2.settimeout(1)
            sock2.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock2.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock2.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock2.connect(Nport2_ip_port)
            my_logger.info("sock2 Rain connect")
            g_sock2_flag = 0
            g_socket_list.append(sock2)
            os.system("echo \"0\" > /tmp/Nport2_status")
            os.system("sync")
        except:
            my_logger.info("sock2 Rain Meter connect error")
            g_sock2_flag = -1
            close_socket(sock2)
            os.system("echo \"-1\" > /tmp/Nport2_status")
            os.system("sync")
            pass

    # Application Server
    elif name == Application_Server_ip_port:
        try:
            sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock3.settimeout(1)
            sock3.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock3.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock3.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock3.connect(Application_Server_ip_port)
            my_logger.info("sock3 Application Server connect")
            g_sock3_flag = 0
            g_socket_list.append(sock3)
        except:
            my_logger.info("sock3 Application Server connect error")
            g_sock3_flag = -1
            close_socket(sock3)
            pass

"""
Use to fine the dot symble in the receive string
"""
def findStr(string, subStr, findCnt):
    listStr = string.split(subStr,findCnt)
    if len(listStr) <= findCnt:
        return -1
    return len(string)-len(listStr[-1])-len(subStr)

"""
Main function will check the sock status in while loop. sock1: Water Meter, sock2: Rain Meter, sock3: application Server
"""
def main():
    global sock1
    global sock2
    global sock3
    global g_sock1_flag
    global g_sock2_flag
    global g_sock3_flag
    global g_socket_list

    global_check_dongle_exist = False
    for devPath in USB_DEV_ARRAY:
        #my_logger.info(devPath)
        ser = get_lora_module_addr(devPath)
        if ser is None:
            continue
        else:
            global_check_dongle_exist = True
            #my_logger.info("Open LoRa node done:")
            #my_logger.info(devPath)
            break
    # clean_session=True, userdata=None, protocol=MQTTv311, transport="tcp"
    client = mqtt.Client(protocol=mqtt.MQTTv31)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("localhost", 1883, 60)

    client.loop_start()
    Create_DB()
    dot_str = ','
    global Sensor_Count
    while True:

        # check connect status
        if g_sock1_flag == -1:
            TCP_connect(Nport1_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_NPORT1_IP + ':' + NETSTAT_NPORT1_PORT + '|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock1_flag = -1
                    close_socket(sock1)
            if g_sock1_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_NPORT1_IP + ':' + NETSTAT_NPORT1_PORT+ '|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info(res_return)
                        g_sock1_flag = -1
                        close_socket(sock1)

        # check connect status
        if g_sock2_flag == -1:
            TCP_connect(Nport2_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_NPORT2_IP + ':' + NETSTAT_NPORT2_PORT + '|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock2_flag = -1
                    close_socket(sock2)
            if g_sock2_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_NPORT2_IP + ':' + NETSTAT_NPORT2_PORT + '|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info(res_return)
                        g_sock2_flag = -1
                        close_socket(sock2)

        # check connect status
        if g_sock3_flag == -1:
            TCP_connect(Application_Server_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_APPLICATION_IP + ':' + NETSTAT_APPLICATION_PORT + '|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock3_flag = -1
                    close_socket(sock3)
            if g_sock3_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_APPLICATION_IP + ':' + NETSTAT_APPLICATION_PORT + '|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info(res_return)
                        g_sock3_flag = -1
                        close_socket(sock3)

        try:
            #Await a read event
            rlist, wlist, elist = select.select( g_socket_list, [], [], SELECT_TIMEOUT)
        except select.error:
            my_logger.info("select error")

        for sock in rlist:
            if sock1 == sock: #water
                try:
                    recvdata = sock.recv(1024)
                    if recvdata:
                        my_logger.info("received Water:"+str(recvdata))
                        #parser status from recvdata
                        for index in range(1,6):
                            if index ==1:
                                first_dot = findStr(recvdata,dot_str,index)
                            elif index ==2:
                                second_dot = findStr(recvdata,dot_str,index)
                            elif index ==3:
                                third_dot = findStr(recvdata,dot_str,index)
                            elif index ==4:
                                forth_dot = findStr(recvdata,dot_str,index)
                            elif index ==5:
                                fivth_dot = findStr(recvdata,dot_str,index)
                        my_logger.info("Total str Length:"+str(len(recvdata)))
                        lastdotindex = recvdata.rfind(dot_str)
                        my_logger.info("lastdotindex:"+str(lastdotindex))
                        Water = recvdata[first_dot+1:second_dot]
                        my_logger.info("Water:"+str(Water))
                        Power_status = recvdata[second_dot+1:third_dot]
                        my_logger.info("Power_status:"+str(Power_status))
                        Voltage_status = recvdata[third_dot+1:forth_dot]
                        my_logger.info("Voltage_status:"+str(Voltage_status))
                        Reserve_status_1 = recvdata[forth_dot+1:fivth_dot]
                        my_logger.info("Reserve_status_1:"+str(Reserve_status_1))
                        Reserve_status_2 = recvdata[fivth_dot+1:len(recvdata)]
                        my_logger.info("Reserve_status_2:"+str(Reserve_status_2))
                        Status = (int(Power_status))<<0 | (int(Voltage_status))<<1 | (int(Reserve_status_1))<<2 | (int(Reserve_status_2)) <<3
                        my_logger.info("Status:"+str(Status))
                        # convert to dec
                        try:
                            Water_float = round(float(Water),2)
                        except:
                            Water_float =0
                        try:
                            Water_int = int(float(Water_float))
                        except:
                            Water_int =0
                        Water_decimal = int(round((Water_float - Water_int),2)*100)
                        Command = 0<<2
                        Data_Type = 1<<0
                        Command_MAC_Level = Self_MAC_Level<<5
                        Time = int(time.time())
                        #Timestamp = binascii.hexlify(struct.pack(Endian + 'I', Time))
                        CMD= Command_MAC_Level | Command | Data_Type
                        # pack format
                        Water_format = binascii.hexlify(struct.pack(Endian + 'BLHBB', CMD, Time, Water_int, Water_decimal,Status))
                        my_logger.info(Water_format)
                        if Sensor_Count == 9999:
                            Sensor_Count = 1
                        else:
                            Sensor_Count +=1
                        my_logger.info("Sensor count:"+str(Sensor_Count))
                        connect_DB_put_data(1, MAC_Address, Water_format, Sensor_Count)
                    if not recvdata:
                        my_logger.info("sock1 Water Meter disconnect")
                        g_sock1_flag = -1
                        close_socket(sock1)
                except socket.error:
                    my_logger.info("sock1 Water Meter socket error")
                    g_sock1_flag = -1
                    close_socket(sock1)
            elif sock2 == sock: #rain
                try:
                    recvdata = sock.recv(1024)
                    if recvdata:
                        my_logger.info("received Rain:"+str(recvdata))
                        #parser status from recvdata
                        for index in range(1,6):
                            if index ==1:
                                first_dot = findStr(recvdata,dot_str,index)
                            elif index ==2:
                                second_dot = findStr(recvdata,dot_str,index)
                            elif index ==3:
                                third_dot = findStr(recvdata,dot_str,index)
                            elif index ==4:
                                forth_dot = findStr(recvdata,dot_str,index)
                            elif index ==5:
                                fivth_dot = findStr(recvdata,dot_str,index)
                        my_logger.info("Total str Length:"+str(len(recvdata)))
                        lastdotindex = recvdata.rfind(dot_str)
                        my_logger.info("lastdotindex:"+str(lastdotindex))
                        Rain = recvdata[first_dot+1:second_dot]
                        my_logger.info("Rain:"+str(Rain))
                        Power_status = recvdata[second_dot+1:third_dot]
                        my_logger.info("Power_status:"+str(Power_status))
                        Voltage_status = recvdata[third_dot+1:forth_dot]
                        my_logger.info("Voltage_status:"+str(Voltage_status))
                        Reserve_status_1 = recvdata[forth_dot+1:fivth_dot]
                        my_logger.info("Reserve_status_1:"+str(Reserve_status_1))
                        Reserve_status_2 = recvdata[fivth_dot+1:len(recvdata)]
                        my_logger.info("Reserve_status_2:"+str(Reserve_status_2))
                        Status = (int(Power_status))<<0 | (int(Voltage_status))<<1 | (int(Reserve_status_1))<<2 | (int(Reserve_status_2)) <<3
                        my_logger.info("Status:"+str(Status))
                        # convert to dec
                        try:
                            Rain_float = round(float(Rain),2)
                            my_logger.info("Rain_float:"+str(Rain_float))
                        except:
                            Rain_float =0
                        try:
                            Rain_int = int(float(Rain_float))
                            my_logger.info("Rain_int:"+str(Rain_int))
                        except:
                            Rain_int =0
                        Rain_decimal = int(round((Rain_float - Rain_int),2)*100)
                        my_logger.info("Rain_decimal:"+str(Rain_decimal))
                        Command = 0<<2
                        Data_Type = 1<<1
                        Command_MAC_Level = Self_MAC_Level<<5
                        Time = int(time.time())
                        #Timestamp = binascii.hexlify(struct.pack(Endian + 'I', Time))
                        CMD= Command_MAC_Level | Command | Data_Type
                        # pack format
                        Rain_format = binascii.hexlify(struct.pack(Endian + 'BLHBB', CMD, Time, Rain_int, Rain_decimal,Status))
                        my_logger.info(Rain_format)
                        if Sensor_Count == 9999:
                            Sensor_Count = 1
                        else:
                            Sensor_Count +=1
                        my_logger.info("Sensor count:"+str(Sensor_Count))
                        connect_DB_put_data(2, MAC_Address, Rain_format, Sensor_Count)
                    if not recvdata:
                        my_logger.info("sock2 Rain Meter disconnect")
                        g_sock2_flag = -1
                        close_socket(sock2)
                except socket.error:
                    my_logger.info("sock2 Rain Meter socket error")
                    g_sock2_flag = -1
                    close_socket(sock2)
            elif sock3 == sock: #Application server
                try:
                    recvdata = sock.recv(1024)
                    if recvdata:
                        my_logger.info("received Application Server Data:"+str(recvdata))
                        #parser receive data is correction time or retransmit command
                        command = recvdata[8:10]
                        # correction time command
                        if command == '04':
                            datalen = len(recvdata)
                            if datalen == 18:
                                my_logger.info("received correction time command")
                                server_mac_address = recvdata[0:8]
                                my_logger.info("server_mac_address: "+str(server_mac_address))
                                data = recvdata[8:18]
                                if Sensor_Count == 9999:
                                    Sensor_Count = 1
                                else:
                                    Sensor_Count +=1
                                connect_DB_put_data(4, server_mac_address, data , Sensor_Count)
                            else:
                                my_logger.info("received correction time command but length error!!!")
                        # retransmit command
                        elif command == '09' or command == '0a':
                            datalen = len(recvdata)
                            if datalen == 20:
                                my_logger.info("received retransmit command")
                                retransmit_mac_address = recvdata[0:8]
                                data = recvdata[8:20]
                                if Sensor_Count == 9999:
                                    Sensor_Count = 1
                                else:
                                    Sensor_Count +=1
                                data = data + retransmit_mac_address
                                connect_DB_put_data(5, MAC_Address, data, Sensor_Count)
                            else:
                                my_logger.info("received retransmit command but length error!!!")
                        else:
                            my_logger.info("received unknow command")
                        #try:
                         #   Rain_int = int(Rain)
                        #except ValueError:
                         #   Rain_int = 0
                    if not recvdata:
                        my_logger.info("sock3 Application Server disconnect")
                        g_sock3_flag = -1
                        close_socket(sock3)
                except socket.error:
                    my_logger.info("sock3 Application Server socket error")
                    g_sock3_flag = -1
                    close_socket(sock3)
            else:
                my_logger.info("Socket Else")

if __name__ == "__main__":
    main()
