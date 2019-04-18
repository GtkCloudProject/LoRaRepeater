#!/usr/bin/python

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
MY_MQTT_QUEUE_FILE_PATH = "/var/lora_repeater/queue/"
MY_SENDING_FILE_PATH = "/var/lora_repeater/sending/"
MY_SENT_FILE_PATH = "/var/lora_repeater/sent/"
MY_SEND_FAIL_FILE_PATH = "/var/lora_repeater/fail/"
MY_LOG_FILE_PATH = "/var/lora_repeater/log/"

MY_LOG_FILENAME = MY_LOG_FILE_PATH + "inq.log"
REPLY_STRING = "+CDEVADDR:"
my_dict = {}

Nport1_ip_port = ('192.168.127.88',4001) #water meter
Nport2_ip_port = ('192.168.127.88',4002) #rain meter
Nport3_ip_port = ('192.168.127.88',4003) #radio
Nport4_ip_port = ('192.168.127.88',4004) #display
Diagnosis_PC_ip_port = ('192.168.127.99',4005)
Application_Server_ip_port = ('192.168.127.101',4006)
Microwave_PC_ip_port = ('192.168.127.102',4007)

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

#To close socket
def close_socket(sock_c):
    global g_socket_list

    sock_c.close()
    try:
        g_socket_list.remove(sock_c)
    except ValueError:
        pass

#get MAC Address for serial
def get_lora_module_addr(dev_path):
    try:
        ser = serial.Serial(dev_path, 9600, timeout=0.5)
        ser.flushInput()
        ser.flushOutput()
        ser.write("AT+cdevaddr?\r\n")
        #time.sleep(3)
        check_my_dongle = str(ser.readlines())
        #print check_my_dongle
        global MAC_Address, Self_MAC_Level
        MAC_Address = check_my_dongle[check_my_dongle.find(REPLY_STRING) + 10: check_my_dongle.find(REPLY_STRING) + 18]
        print "MAC_Address:",MAC_Address
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
            print "MAC Level Error reset to 0"
        #my_logger.info('My USB dongle checked')
        return ser
        #else:
            #return None
    except serial.serialutil.SerialException:
        # print 'FAIL: Cannot open Serial Port (No LoRa Node Inserted)'
        return None
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
            print("connect to DB")
            sql = "create database if not exists sensor"
            cursor.execute(sql)
            cursor.execute("USE sensor")
            print("create sensordata table to DB")
            sql = "create table if not exists sensordata(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, retransmit_flag BOOLEAN NOT NULL default 0, frame_count INT NOT NULL, last_sent_time timestamp NOT NULL, UNIQUE(source_mac_address, time, frame_count))"
            cursor.execute(sql)
            print("create correctiontime table to DB")
            sql = "create table if not exists correctiontime(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, frame_count INT NOT NULL, last_sent_time timestamp NOT NULL, UNIQUE(source_mac_address, time))"
            cursor.execute(sql)
            print("create retransmission table to DB")
            sql = "create table if not exists retransmission(source_mac_address CHAR(8) NOT NULL,time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, raw_data CHAR(22), sended_flag BOOLEAN NOT NULL default 0, frame_count INT NOT NULL, last_sent_time timestamp NOT NULL, UNIQUE(source_mac_address, time, frame_count))"
            cursor.execute(sql)
    finally:
        print("connection close!")

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
                print("connect to DB")
                cursor.execute("USE sensor")
                print "p_sensor_mac:",p_sensor_mac
                SourceMACAddress = MAC_Address
                if db_type == 1:
                    print("parameter = Water")
                    sql = "select * from sensordata"
                    number_of_rows = cursor.execute(sql)
                    print"number_of_rows is:",number_of_rows
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        print"Delete number_of_rows is:",del_number
                        sql = "delete from sensordata order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', %s)" % (SourceMACAddress, time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                    cursor.execute(sql)
                    connection.commit()
                elif db_type == 2:
                    print("parameter = Rain")
                    sql = "select * from sensordata"
                    number_of_rows = cursor.execute(sql)
                    print"number_of_rows is:",number_of_rows
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        print"Delete number_of_rows is:",del_number
                        sql = "delete from sensordata order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', %s)" % (SourceMACAddress, time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                    cursor.execute(sql)
                    connection.commit()
                elif db_type == 3:
                    print("parameter = Lora")
                    sql = "select * from sensordata"
                    number_of_rows = cursor.execute(sql)
                    print"number_of_rows is:",number_of_rows
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        print"Delete number_of_rows is:",del_number
                        sql = "delete from sensordata order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', '%s')" % (p_sensor_mac,time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                    cursor.execute(sql)
                    connection.commit()
                elif db_type == 4:
                    print("parameter = Correction Time")
                    sql = "select * from correctiontime"
                    number_of_rows = cursor.execute(sql)
                    print"number_of_rows is:",number_of_rows
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        print"Delete number_of_rows is:",del_number
                        sql = "delete from correctiontime order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    sql = "select sended_flag, raw_data, source_mac_address, frame_count, last_sent_time from correctiontime WHERE last_sent_time > DATE_SUB(now(), INTERVAL 2 MINUTE) and last_sent_time < now() and source_mac_address='%s'" % (p_sensor_mac)
                    cursor.execute(sql)
                    print "cursor.rowcount:",cursor.rowcount
                    if(cursor.rowcount==0):
                        sql = "insert ignore into correctiontime (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', '%s') ON DUPLICATE KEY UPDATE sended_flag =0, last_sent_time=now()" % (p_sensor_mac,time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                        cursor.execute(sql)
                        connection.commit()
                        if 'ffffff' in p_sensor_mac or 'FFFFFF' in p_sensor_mac:
                            #replace system time here by nick
                            print("Replace system time!!!")
                            strtime = time.strftime('%Y-%m-%d %H:%M:%S',tmp_time)
                            print "strtime:",strtime
                            os.system('date -s "%s"' % strtime)
                    else:
                        print("Replace system time, wait colddown 2 mins")
                elif db_type == 5:
                    print("parameter = Retransmition")
                    sql = "select * from retransmission"
                    number_of_rows = cursor.execute(sql)
                    print"number_of_rows is:",number_of_rows
                    if number_of_rows > MAX_DB_Count:
                        del_number = number_of_rows - MAX_DB_Count
                        print"Delete number_of_rows is:",del_number
                        sql = "delete from retransmission order by time limit %s" % del_number
                        cursor.execute(sql)
                        connection.commit()
                    tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                    time_interval = int(p_sensor_data[10:12],16)
                    print "time_interval:",time_interval
                    sql = "select sended_flag, raw_data, source_mac_address, frame_count, last_sent_time from retransmission WHERE last_sent_time > DATE_SUB(now(), INTERVAL 2 MINUTE) and source_mac_address='%s' and time='%s'" % (p_sensor_mac, time.strftime('%Y-%m-%d %H:%M:%S',tmp_time))
                    cursor.execute(sql)
                    print "cursor.rowcount:",cursor.rowcount
                    if(cursor.rowcount==0):
                        sql = "insert ignore into retransmission(source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', '%s') ON DUPLICATE KEY UPDATE sended_flag =0, last_sent_time=now()" % (p_sensor_mac,time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), p_sensor_data, p_sensor_count)
                        cursor.execute(sql)
                        connection.commit()
                    else:
                        print("update sended_flag fail, wait colddown 2 mins")
        finally:
            print("connection close!")
            connection.close()
        g_db_mutex.release()

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
            print("connect to DB select data")
            cursor.execute("USE sensor")
            print "sensor_mac:",sensor_mac
            if db_type == 1:
                sql = "select sended_flag, retransmit_flag, raw_data, source_mac_address, frame_count, last_sent_time from sensordata WHERE last_sent_time > DATE_SUB(now(), INTERVAL 2 MINUTE) and retransmit_flag =1"
                cursor.execute(sql)
                print "cursor.rowcount:",cursor.rowcount
                if(cursor.rowcount==0):
                    sql = "select source_mac_address, sended_flag, retransmit_flag, raw_data, frame_count from sensordata WHERE time >='%s' and time < DATE_ADD('%s', INTERVAL '%s' MINUTE) and source_mac_address='%s'" % (time, time, time_interval, sensor_mac)
                    cursor.execute(sql)
                    print "cursor.rowcount:",cursor.rowcount
                    if(cursor.rowcount>0):
                        for index in range(cursor.rowcount):
                            print "index:",index
                            if Sensor_Count == 9999:
                                Sensor_Count = 1
                            else:
                                Sensor_Count +=1
                            print"Sensor count:"+str(Sensor_Count)
                            sql = "UPDATE sensordata SET retransmit_flag =1, frame_count='%s', last_sent_time=now() where time >='%s' and time < DATE_ADD('%s', INTERVAL '%s' MINUTE) and source_mac_address='%s' and retransmit_flag =0 limit 1" % (Sensor_Count, time, time, time_interval, sensor_mac)
                            cursor.execute(sql)
                            connection.commit()
                else:
                    print("select retransmit data, update retransmit_flag fail, wait colddown 2 mins")
            elif db_type == 2:
                sql = "select * from sensordata"
                number_of_rows = cursor.execute(sql)
                print"number_of_rows is:",number_of_rows
                if number_of_rows > MAX_DB_Count:
                    del_number = number_of_rows - MAX_DB_Count
                    print"Delete number_of_rows is:",del_number
                    sql = "delete from sensordata order by time limit %s" % del_number
                    cursor.execute(sql)
                    connection.commit()
                sql = "select sended_flag, retransmit_flag, raw_data, source_mac_address, frame_count, last_sent_time from sensordata WHERE last_sent_time > DATE_SUB(now(), INTERVAL 2 MINUTE) and source_mac_address='%s' and frame_count='%s'" % (sensor_mac, sensor_count)
                cursor.execute(sql)
                if(cursor.rowcount==0):
                    sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count, sended_flag, retransmit_flag) values('%s', '%s', '%s', '%s', 1, 1) ON DUPLICATE KEY UPDATE retransmit_flag =1, last_sent_time=now()" % (sensor_mac, time, sensor_data, sensor_count)
                    cursor.execute(sql)
                    connection.commit()
                else:
                    print("select retransmit ACK data, update retransmit_flag fail, wait colddown 2 mins")
    finally:
        print("connection close!")
        connection.close()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    # print("Connected with result code "+str(rc))
    print('Mqtt Connected.')
    client.subscribe("#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global Sensor_Count
    json_count1 = 0
    try:
        # print(msg.topic+" "+str(msg.payload))
        #print('Message incoming')
        #print(msg.topic)
        #print(msg.payload)
        json_data = msg.payload
        json_array_size = len(json.loads(json_data))
        while json_count1 < json_array_size:
            sensor_mac = json.loads(json_data)[json_count1]['macAddr']
            sensor_data = json.loads(json_data)[json_count1]['data']
            sensor_count = json.loads(json_data)[json_count1]['frameCnt']
            nFrameCnt = json.loads(json_data)[json_count1]['frameCnt']
            print"Data is:",sensor_data
            Data_Len = len(sensor_data)
            print"Data_Len is:",Data_Len
            print"sensor_count is:",sensor_count
            Command = int(sensor_data[0:2],16)
            recv_mac_level = Command>>5
            CMD = (Command>>2) & ~( 1<<3 | 1<<4 | 1<<5)
            Data_type = Command & ~( 1<<2 | 1<<3 | 1<<4 | 1<<5 | 1<<6 | 1<<7 )
            # Store data to DB
            # Check the command if not sensor data do not insert to DB
            if CMD == 0 and (Data_type == 1 or Data_type == 2):
                print"Receive Sensor data from lora"
                if Self_MAC_Level >= recv_mac_level:
                    print("Ready to put sensor data to DB")
                    connect_DB_put_data(3, sensor_mac[8:16], sensor_data, sensor_count)
            elif Data_type == 0 and CMD == 1:
                print("Receive Correction Lora Packet")
                print "MAC_Address:",MAC_Address
                print "sensor_mac[8:16]:",sensor_mac[8:16]
                if 'ffffff' in sensor_mac[8:16] or 'FFFFFF' in sensor_mac[8:16]:
                    print("Receive Broadcast Correction Packet")
                    #pepare correction time ack
                    if Self_MAC_Level <= recv_mac_level:
                        print("Ready to put correction time data to DB")
                        connect_DB_put_data(4, sensor_mac[8:16], sensor_data, sensor_count) #forward broadcast correction time
                        if Sensor_Count == 9999:
                            Sensor_Count = 1
                        else:
                            Sensor_Count +=1
                        print"Sensor count:"+str(Sensor_Count)
                        connect_DB_put_data(4, MAC_Address, sensor_data, Sensor_Count) #send ack correction
                else:
                    if Self_MAC_Level >= recv_mac_level:
                        print("Forward Correction 'ACK' Packet")
                        connect_DB_put_data(4, sensor_mac[8:16], sensor_data, sensor_count)#forward ack correction
            elif (Data_type == 1 or Data_type == 2) and CMD == 2 and Data_Len == 20:
                print("Receive Retransmit Lora Packet")
                #select witch sensor data need to retransmit
                retransmit_time = sensor_data[2:10]
                tmp_time = time.localtime(int(retransmit_time,16))
                strtime = time.strftime('%Y-%m-%d %H:%M:%S',tmp_time)
                print "strtime:",strtime
                time_interval = int(sensor_data[10:12],16)
                print "time_interval:",time_interval
                if Self_MAC_Level <= recv_mac_level:
                    print("Ready to put retransmit data to DB")
                    connect_DB_put_data(5, sensor_mac[8:16], sensor_data, sensor_count)
                if sensor_data[12:20] == MAC_Address:
                    print("Select Re-transmit data from DB")
                    connect_DB_select_data(1, sensor_data[12:20], strtime, time_interval, sensor_data , sensor_count)
            elif (Data_type == 1 or Data_type == 2) and CMD == 2 and Data_Len == 18:
                print"Receive Retransmit ACK data from lora"
                if Self_MAC_Level > recv_mac_level:
                    print("Ready to put Retransmit sensor data to DB")
                    #select witch sensor data need to retransmit
                    retransmit_time = sensor_data[2:10]
                    tmp_time = time.localtime(int(retransmit_time,16))
                    strtime = time.strftime('%Y-%m-%d %H:%M:%S',tmp_time)
                    print "strtime:",strtime
                    time_interval = 0
                    #print "time_interval:",time_interval
                    connect_DB_select_data(2, sensor_mac[8:16], strtime, time_interval, sensor_data , sensor_count)
            else:
                print("not sensor data lora packet")
                print(sensor_data)
                if sensor_data == LORA_VERIFY_STR:
                    os.system("echo \"0\" > /tmp/lora_status")
                    os.system("sync")
            json_count1 = json_count1 + 1

    except:
        print('Received a non-UTF8 msg')

def TCP_connect(name):
    global sock1
    global sock2
    global sock3
    global g_sock1_flag
    global g_sock2_flag
    global g_sock3_flag

    if name == Nport1_ip_port:
        try:
            sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock1.settimeout(1)
            sock1.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock1.connect(Nport1_ip_port)
            print ("sock1 Water Meter connect")
            g_sock1_flag = 0
            g_socket_list.append(sock1)
            os.system("echo \"0\" > /tmp/Nport1_status")
            os.system("sync")
        except:
            print("sock1 Water Meter connect error")
            g_sock1_flag = -1
            close_socket(sock1)
            os.system("echo \"-1\" > /tmp/Nport1_status")
            os.system("sync")
            pass
    elif name == Nport2_ip_port:
        try:
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock2.settimeout(1)
            sock2.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock2.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock2.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock2.connect(Nport2_ip_port)
            print ("sock2 Rain connect")
            g_sock2_flag = 0
            g_socket_list.append(sock2)
            os.system("echo \"0\" > /tmp/Nport2_status")
            os.system("sync")
        except:
            print("sock2 Rain Meter connect error")
            g_sock2_flag = -1
            close_socket(sock2)
            os.system("echo \"-1\" > /tmp/Nport2_status")
            os.system("sync")
            pass
    elif name == Application_Server_ip_port:
        try:
            sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock3.settimeout(1)
            sock3.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock3.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock3.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock3.connect(Application_Server_ip_port)
            print ("sock3 Application Server connect")
            g_sock3_flag = 0
            g_socket_list.append(sock3)
        except:
            print("sock3 Application Server connect error")
            g_sock3_flag = -1
            close_socket(sock3)
            pass

def main():
    global sock1
    global sock2
    global sock3
    global g_sock1_flag
    global g_sock2_flag
    global g_sock3_flag
    global g_socket_list

    # start:
    # make queue file folder
    if not os.path.exists(MY_MQTT_QUEUE_FILE_PATH):
        os.makedirs(MY_MQTT_QUEUE_FILE_PATH)
    # make sending file folder
    if not os.path.exists(MY_SENDING_FILE_PATH):
        os.makedirs(MY_SENDING_FILE_PATH)
    # make sent file folder
    if not os.path.exists(MY_SENT_FILE_PATH):
        os.makedirs(MY_SENT_FILE_PATH)
    # make sending fail file folder
    if not os.path.exists(MY_SEND_FAIL_FILE_PATH):
        os.makedirs(MY_SEND_FAIL_FILE_PATH)
    # make log file folder
    if not os.path.exists(MY_LOG_FILE_PATH):
        os.makedirs(MY_LOG_FILE_PATH)

    # Set up a specific logger with our desired output level
    my_logger = logging.getLogger('enqueue')
    # Add the log message handler to the logger
    my_logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(MY_LOG_FILENAME, maxBytes=10240, backupCount=100)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
    print('inq.py is started!')
# example
# my_logger.debug('debug message')
# print('info message')
# my_logger.warn('warn message')
# my_logger.error('error message')
# my_logger.critical('critical message')

    global_check_dongle_exist = False
    for devPath in USB_DEV_ARRAY:
        #print devPath
        ser = get_lora_module_addr(devPath)
        if ser is None:
            continue
        else:
            global_check_dongle_exist = True
            #print('Open LoRa node done:')

            #print(devPath)
            break

    # clean_session=True, userdata=None, protocol=MQTTv311, transport="tcp"
    client = mqtt.Client(protocol=mqtt.MQTTv31)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("localhost", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
#client.loop_forever()

    client.loop_start()
    Create_DB()
    dot_str = ','
    global Sensor_Count
    while True:
        if g_sock1_flag == -1:
            TCP_connect(Nport1_ip_port)
        if g_sock2_flag == -1:
            TCP_connect(Nport2_ip_port)
        if g_sock3_flag == -1:
            TCP_connect(Application_Server_ip_port)

        try:
            #Await a read event
            #rlist, wlist, elist = select.select( [sock1, sock2, sock3], [], [], 5)
            rlist, wlist, elist = select.select( g_socket_list, [], [], SELECT_TIMEOUT)
        except select.error:
            print "select error"

        for sock in rlist:
            if sock1 == sock: #water
                try:
                    recvdata = sock.recv(1024)
                    if recvdata:
                        print "received Water:"+str(recvdata)
                        recvstr = recvdata[recvdata.find(dot_str) + 1:]
                        print "recvstr:",recvstr
                        if dot_str in recvstr: #find 2nd dot_str
                            Water = recvstr[0:recvstr.find(dot_str)]
                            print "Water:",Water
                            Status = int(recvstr[recvstr.find(dot_str) +1:],16)
                            print "Status:",Status
                        else: #no 2nd dot_str
                            Water = recvstr[0:recvstr.find(dot_str)]
                            print "Water:",Water
                            Status = 255
                            print "Status:",Status
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
                        Water_format = binascii.hexlify(struct.pack(Endian + 'BLHBB', CMD, Time, Water_int, Water_decimal,Status))
                        print Water_format
                        if Sensor_Count == 9999:
                            Sensor_Count = 1
                        else:
                            Sensor_Count +=1
                        print"Sensor count:"+str(Sensor_Count)
                        connect_DB_put_data(1, MAC_Address, Water_format, Sensor_Count)
                    if not recvdata:
                        print "sock1 Water Meter disconnect"
                        g_sock1_flag = -1
                        close_socket(sock1)
                except socket.error:
                    print "sock1 Water Meter socket error"
                    g_sock1_flag = -1
                    close_socket(sock1)
                    time.sleep(5)
            elif sock2 == sock: #rain
                try:
                    recvdata = sock.recv(1024)
                    if recvdata:
                        print "received Rain:"+str(recvdata)
                        recvstr = recvdata[recvdata.find(dot_str) + 1:]
                        print "recvstr:",recvstr
                        if dot_str in recvstr: #find 2nd dot_str
                            Rain = recvstr[0:recvstr.find(dot_str)]
                            print "Rain:",Rain
                            Power_status = int(recvstr[recvstr.find(dot_str) +1:])
                            print "Power_status:",Power_status
                        else: #no 2nd dot_str
                            Rain = recvstr[0:recvstr.find(dot_str)]
                            print "Rain:",Rain
                            Power_status = 1
                            print "Power_status:",Power_status
                        try:
                            Rain_float = round(float(Rain),2)
                            print "Rain_float:",Rain_float
                        except:
                            Rain_float =0
                        try:
                            Rain_int = int(float(Rain_float))
                            print "Rain_int:",Rain_int
                        except:
                            Rain_int =0
                        Rain_decimal = int(round((Rain_float - Rain_int),2)*100)
                        print "Rain_decimal:",Rain_decimal
                        Command = 0<<2
                        Data_Type = 1<<1
                        Command_MAC_Level = Self_MAC_Level<<5
                        Time = int(time.time())
                        #Timestamp = binascii.hexlify(struct.pack(Endian + 'I', Time))
                        CMD= Command_MAC_Level | Command | Data_Type
                        Rain_format = binascii.hexlify(struct.pack(Endian + 'BLHBB', CMD, Time, Rain_int, Rain_decimal,Power_status))
                        print Rain_format
                        if Sensor_Count == 9999:
                            Sensor_Count = 1
                        else:
                            Sensor_Count +=1
                        print "Sensor count:"+str(Sensor_Count)
                        connect_DB_put_data(2, MAC_Address, Rain_format, Sensor_Count)
                    if not recvdata:
                        print "sock2 Rain Meter disconnect"
                        g_sock2_flag = -1
                        close_socket(sock2)
                except socket.error:
                    print "sock2 Rain Meter socket error"
                    g_sock2_flag = -1
                    close_socket(sock2)
                    time.sleep(5)
            elif sock3 == sock: #Application server
                try:
                    recvdata = sock.recv(1024)
                    if recvdata:
                        print "received Application Server Data:"+str(recvdata)
                        #parser receive data is correction time or retransmit command
                        command = recvdata[8:10]
                        if command == '04':
                            datalen = len(recvdata)
                            if datalen == 18:
                                print "received correction time command"
                                server_mac_address = recvdata[0:8]
                                #print "server_mac_address",server_mac_address
                                data = recvdata[8:18]
                                if Sensor_Count == 9999:
                                    Sensor_Count = 1
                                else:
                                    Sensor_Count +=1
                                connect_DB_put_data(4, server_mac_address, data , Sensor_Count)
                            else:
                                print "received correction time command but length error!!!"
                        elif command == '09' or command == '0a':
                            datalen = len(recvdata)
                            if datalen == 20:
                                print "received retransmit command"
                                retransmit_mac_address = recvdata[0:8]
                                data = recvdata[8:20]
                                if Sensor_Count == 9999:
                                    Sensor_Count = 1
                                else:
                                    Sensor_Count +=1
                                data = data + retransmit_mac_address
                                connect_DB_put_data(5, MAC_Address, data, Sensor_Count)
                            else:
                                print "received retransmit command but length error!!!"
                        else:
                            print "received unknow command"
                        #try:
                         #   Rain_int = int(Rain)
                        #except ValueError:
                         #   Rain_int = 0
                    if not recvdata:
                        print "sock3 Application Server disconnect"
                        g_sock3_flag = -1
                        close_socket(sock3)
                except socket.error:
                    print "sock3 Application Server socket error"
                    g_sock3_flag = -1
                    close_socket(sock3)
                    time.sleep(5)
            else:
                print"Socket Else"

if __name__ == "__main__":
    main()
