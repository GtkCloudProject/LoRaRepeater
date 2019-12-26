#!/usr/bin/python

"""
@file deq.py
@brief a. forward sensor's data withch store in database and send that by LoRa module.
       b. forward sensor's data, correction time ack and retransmission ack data to application server by ethernet socket.
       c. forward correction time command
       d. forward retransmission command
@author Nick Lee / Chris Chang
@date 2019/06
"""

#System Imports
import os
import json
import sys
import time
import serial
import logging
import pymysql.cursors
import socket,select
import struct
import binascii
import subprocess
from logging.handlers import RotatingFileHandler
import crcmod.predefined
from binascii import unhexlify

USB_DEV_ARRAY = ["/dev/ttyS0"]

MY_SLEEP_INTERVAL = 4.5
MY_ALIVE_INTERVAL = 86400

MY_LOG_FILE_PATH = "/mnt/data/Ftpdir/"
MY_LOG_FILENAME = MY_LOG_FILE_PATH + "deq.log"

MY_NODE_MAC_ADDR = ""
MY_NODE_MAC_ADDR_SHORT = ""

GLOBAL_TIME_RUNNING = 0
GLOBAL_COUNT_SENT = 0
GLOBAL_COUNT_FAIL = 0

SENT_OK_TAG = "Radio Tx Done\r\n"
REPLY_OK_STRING = "OK"
REPLY_STRING = "+CDEVADDR:"

Data_need_to_send = None
Correction_Time_need_to_send = None
Retransmission_need_to_send = None
g_Frame_Count = 0
g_Sended_Flag = ""
g_Retransmit_Flag = ""
Source_MAC_address = ""

g_minCnt = 0
g_minCnt_tbl_name = ""

NETSTAT_NPORT3_IP = "10.56.147.241"
NETSTAT_NPORT3_PORT = "4003"
NETSTAT_NPORT4_IP = "10.56.147.241"
NETSTAT_NPORT4_PORT = "4004"
NETSTAT_APPLICATION_IP = "10.56.147.176"
NETSTAT_APPLICATION_PORT = "4006"
NETSTAT_DIAGNOSIS_IP = "10.56.147.240"
NETSTAT_DIAGNOSIS_PORT = "4005"
NETSTAT_MICROWAVE_IP = "10.56.147.176"
NETSTAT_MICROWAVE_PORT = "4007"

Nport1_ip_port = ('10.56.147.241',4001) #water meter
Nport2_ip_port = ('10.56.147.241',4002) #rain meter
Nport3_ip_port = ('10.56.147.241',4003) #radio
Nport4_ip_port = ('10.56.147.241',4004) #display
Diagnosis_PC_ip_port = ('10.56.147.240',4005)
Application_Server_ip_port = ('10.56.147.176',4006)
Microwave_PC_ip_port = ('10.56.147.176',4007)

my_dict_appskey = {}
my_dict_nwkskey = {}

MAC_Address=0
Self_MAC_Level=0
Endian = '>' #big-endian

STATUS_OK="OK"
STATUS_FAIL="FAIL"

#Nport socket status
g_Nport1_ip_port_status = 0
g_Nport2_ip_port_status = 0
g_Nport3_ip_port_status = 0
g_Nport4_ip_port_status = 0

#Application Server status
g_Application_Server_ip_port_status = -1

#Microwave_PC status
g_Microwave_PC_ip_port_status = -1

#socket flag
g_sock1_flag = -1
g_sock2_flag = -1
g_sock3_flag = -1
g_sock4_flag = -1
g_sock5_flag = -1

#select socket queue
g_socket_list = []

#select timeout
SELECT_TIMEOUT = 1

#socket UNKNOW status
SOCK_UNKNOW = "unkn"

# Set up a specific logger with our desired output level
my_logger = logging.getLogger('dequeue')
# Add the log message handler to the logger
my_logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(MY_LOG_FILENAME, maxBytes=2048000, backupCount=10)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
my_logger.addHandler(handler)
my_logger.info("deq.py started!!!")
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
        my_logger.info("Closing socket error")
        pass

"""
To show device I/O status
"""
def report_status_to_diagnosis_pc():
    global sock1
    global sock2
    global sock3
    global sock4
    global sock5
    global g_Nport1_ip_port_status
    global g_Nport2_ip_port_status
    global g_Application_Server_ip_port_status
    global g_Microwave_PC_ip_port_status
    global g_sock1_flag
    global MAC_Address

    try:
        my_logger.info("Send sensor data to Diagnosis PC")
        sock1.send("== I/O Status Reporting ==\n")
        #LoRa Repeater FW version
        sub_p = subprocess.Popen("awk -F \"=\" \'{print $(NF)}\' /mnt/data/LoRaRepeater/VERSION", stdout=subprocess.PIPE, shell=True)
        (fw_ver, err) = sub_p.communicate()
        if len(fw_ver) > 0:
            io_status = "LoRa Repeater FW Version: %s" %(fw_ver)
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "LoRa Repeater FW Version: 0.0.0 \n"
            my_logger.info(io_status)
            sock1.send(io_status)

        # MAC address
        if MAC_Address == 0:
            io_status = "Can't get MAC Address\n"
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "MAC Address: %s \n" %(MAC_Address)
            my_logger.info(io_status)
            sock1.send(io_status)

        # LoRa
        sub_p = subprocess.Popen("cat /tmp/lora_status", stdout=subprocess.PIPE, shell=True)
        (lora_status, err) = sub_p.communicate()
        if len(lora_status) > 0:
            lora_status = int(lora_status)
        else:
            lora_status = -1

        if lora_status == 0:
            io_status = "LoRa Status %s \n" %(STATUS_OK)
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "LoRa Status %s \n" %(STATUS_FAIL)
            my_logger.info(io_status)
            sock1.send(io_status)

        # N port port 1
        sub_p = subprocess.Popen("cat /tmp/Nport1_status", stdout=subprocess.PIPE, shell=True)
        (nport1_status, err) = sub_p.communicate()
        if len(nport1_status) > 0:
            g_Nport1_ip_port_status = int(nport1_status)
        else:
            g_Nport1_ip_port_status = -1

        if g_Nport1_ip_port_status == 0:
            io_status = "N Port Port 1 Status %s \n" %(STATUS_OK)
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "N Port Port 1 Status %s \n" %(STATUS_FAIL)
            my_logger.info(io_status)
            sock1.send(io_status)

        # N port port 2
        sub_p = subprocess.Popen("cat /tmp/Nport2_status", stdout=subprocess.PIPE, shell=True)
        (nport2_status, err) = sub_p.communicate()
        if len(nport2_status) > 0:
            g_Nport2_ip_port_status = int(nport2_status)
        else:
            g_Nport2_ip_port_status = -1

        if g_Nport2_ip_port_status == 0:
            io_status = "N Port Port 2 Status %s \n" %(STATUS_OK)
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "N Port Port 2 Status %s \n" %(STATUS_FAIL)
            my_logger.info(io_status)
            sock1.send(io_status)

        # N port port 3
        if g_Nport3_ip_port_status == 0:
            io_status = "N Port Port 3 Status %s \n" %(STATUS_OK)
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "N Port Port 3 Status %s \n" %(STATUS_FAIL)
            my_logger.info(io_status)
            sock1.send(io_status)

        # N port port 4
        if g_Nport4_ip_port_status == 0:
            io_status = "N Port Port 4 Status %s \n" %(STATUS_OK)
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "N Port Port 4 Status %s \n" %(STATUS_FAIL)
            my_logger.info(io_status)
            sock1.send(io_status)

        #Application Server
        if g_Application_Server_ip_port_status == 0:
            io_status = "Application_Server Status %s \n" %(STATUS_OK)
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "Application_Server Status %s \n" %(STATUS_FAIL)
            my_logger.info(io_status)
            sock1.send(io_status)

        #Microwave_PC
        if g_Microwave_PC_ip_port_status == 0:
            io_status = "Microwave PC Status %s \n" %(STATUS_OK)
            my_logger.info(io_status)
            sock1.send(io_status)
        else:
            io_status = "Microwave PC Status %s \n" %(STATUS_FAIL)
            my_logger.info(io_status)
            sock1.send(io_status)

        sock1.send("\n")

    except socket.error:
        my_logger.info("sock1 Diagnosis_PC socket error")
        g_sock1_flag = -1
        close_socket(sock1)

"""
Check socket status, sock1: Diagnosis PC, sock2: Application Server, sock3: Microwave PC sock4: Radio(Not used) sock5: Display
"""
def TCP_connect(name):
    global sock1
    global sock2
    global sock3
    global sock4
    global sock5
    global g_Nport3_ip_port_status
    global g_Nport4_ip_port_status
    global g_Application_Server_ip_port_status
    global g_Microwave_PC_ip_port_status
    global g_sock1_flag
    global g_sock2_flag
    global g_sock3_flag
    global g_sock4_flag
    global g_sock5_flag
    global g_socket_list

    # Diagnosis PC
    if name == Diagnosis_PC_ip_port:
        try:
            sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock1.settimeout(1)
            sock1.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock1.connect(Diagnosis_PC_ip_port)
            my_logger.info("sock1 Diagnosis PC connect")
            g_sock1_flag = 0
            g_socket_list.append(sock1)
        except:
            my_logger.info("sock1 Diagnosis PC connect error")
            g_sock1_flag = -1
            close_socket(sock1)
            pass
    # Application Server
    elif name == Application_Server_ip_port:
        try:
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock2.settimeout(1)
            sock2.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock2.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock2.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock2.connect(Application_Server_ip_port)
            my_logger.info("sock2 Application Server connect")
            g_Application_Server_ip_port_status = 0
            g_sock2_flag = 0
            g_socket_list.append(sock2)
        except:
            my_logger.info("sock2 Application Server connect error")
            g_Application_Server_ip_port_status = -1
            g_sock2_flag = -1
            close_socket(sock2)
            pass
    # Microwave PC
    elif name == Microwave_PC_ip_port:
        try:
            sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock3.settimeout(1)
            sock3.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock3.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock3.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock3.connect(Microwave_PC_ip_port)
            my_logger.info("sock3 Microwave PC connect")
            g_Microwave_PC_ip_port_status = 0
            g_sock3_flag = 0
            g_socket_list.append(sock3)
        except:
            my_logger.info("sock3 Microwave PC connect error")
            g_Microwave_PC_ip_port_status = -1
            g_sock3_flag = -1
            close_socket(sock3)
            pass
    # Radio(Not used)
    elif name == Nport3_ip_port:
        try:
            sock4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock4.settimeout(1)
            sock4.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock4.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock4.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock4.connect(Nport3_ip_port)
            my_logger.info("sock4 Radio connect")
            g_Nport3_ip_port_status = 0
            g_sock4_flag = 0
            g_socket_list.append(sock4)
        except:
            my_logger.info("sock4 Radio connect error")
            g_Nport3_ip_port_status = -1
            g_sock4_flag = -1
            close_socket(sock4)
            pass
    # Display
    elif name == Nport4_ip_port:
        try:
            sock5 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock5.settimeout(1)
            sock5.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock5.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock5.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock5.connect(Nport4_ip_port)
            my_logger.info("sock5 Display connect")
            g_Nport4_ip_port_status = 0
            g_sock5_flag = 0
            g_socket_list.append(sock5)
        except:
            my_logger.info("sock5 Display connect error")
            g_Nport4_ip_port_status = -1
            g_sock5_flag = -1
            close_socket(sock5)
            pass

"""
Use for mapping Lora mac key by group, we using '05' as group id in this project
"""
def build_app_group_table():
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 db='lora',
                                 #charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Read a single record
            # sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
            sql = "SELECT netid_group, appskey, nwkskey  FROM table_netid"
            cursor.execute(sql)
            for row in cursor:
                my_dict_appskey[row["netid_group"]] = row["appskey"]
                my_dict_nwkskey[row["netid_group"]] = row["nwkskey"]
    finally:
        connection.close()

"""
Select which data should be send form three database tables, sensordata, correctiontime and retransmission. If return null, will check again at next time in main whild loop
"""
def get_sensor_data_from_DB(tablename):
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 #db='sensor',
                                 #charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Read a single record
            # sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
            my_logger.info("connect to DB")
            try:
                cursor.execute("USE sensor")
            except:
                connection.rollback()
                my_logger.info("No sensor DB")
            global Source_MAC_address
            global g_Frame_Count
            global g_Sended_Flag
            global g_Retransmit_Flag
            global Data_need_to_send
            global Correction_Time_need_to_send
            global Retransmission_need_to_send
            if tablename == 'sensordata':
                my_logger.info("tablename == sensordata")
                try:
                    # select from sensordata table, get sensor data to be sent
                    sql = "select sended_flag, retransmit_flag, raw_data, source_mac_address, frame_count from sensordata WHERE sended_flag='0' or retransmit_flag='1' order by frame_count limit 1"
                    cursor.execute(sql)
                    #my_logger.info(cursor.rowcount)
                    if(cursor.rowcount>0):
                        for row in cursor:
                            Data_need_to_send = row["raw_data"]
                            Source_MAC_address = row["source_mac_address"]
                            g_Frame_Count = row["frame_count"]
                            g_Sended_Flag = row["sended_flag"]
                            g_Retransmit_Flag = row["retransmit_flag"]
                            my_logger.info("Source_MAC_address: "+str(Source_MAC_address))
                            my_logger.info("Data_need_to_send: "+str(Data_need_to_send))
                            my_logger.info("g_Frame_Count:"+str(g_Frame_Count))
                            my_logger.info("g_Sended_Flag:"+str(g_Sended_Flag))
                            my_logger.info("g_Retransmit_Flag:"+str(g_Retransmit_Flag))
                    else:
                        my_logger.info("DB return null")
                        Data_need_to_send = None
                except:
                    connection.rollback()
            elif tablename == 'correctiontime':
                my_logger.info("tablename == correctiontime")
                try:
                    # select from correctiontime table, get correctiontime data to be sent
                    sql = "select source_mac_address, sended_flag, raw_data, frame_count from correctiontime WHERE sended_flag='0' order by frame_count limit 1"
                    cursor.execute(sql)
                    #my_logger.info(cursor.rowcount)
                    if(cursor.rowcount>0):
                        for row in cursor:
                            Correction_Time_need_to_send = row["raw_data"]
                            g_Frame_Count = row["frame_count"]
                            Source_MAC_address = row["source_mac_address"]
                            my_logger.info("Correction_Time_need_to_send: "+str(Correction_Time_need_to_send))
                            my_logger.info("g_Frame_Count:"+str(g_Frame_Count))
                            my_logger.info("Source_MAC_address: "+str(Source_MAC_address))
                    else:
                        my_logger.info("DB return null")
                        Correction_Time_need_to_send = None
                except:
                    my_logger.info("Correction_Time table except")
                    connection.rollback()
            elif tablename == 'retransmission':
                my_logger.info("tablename == retransmission")
                try:
                    # select from retransmission table, get retransmission data to be sent
                    sql = "select source_mac_address, sended_flag, raw_data, frame_count from retransmission WHERE sended_flag='0' order by frame_count limit 1"
                    cursor.execute(sql)
                    #my_logger.info(cursor.rowcount)
                    if(cursor.rowcount>0):
                        for row in cursor:
                            Retransmission_need_to_send = row["raw_data"]
                            Source_MAC_address = row["source_mac_address"]
                            g_Frame_Count = row["frame_count"]
                            my_logger.info("Source_MAC_address: "+str(Source_MAC_address))
                            my_logger.info("Retransmission_need_to_send: "+str(Retransmission_need_to_send))
                            my_logger.info("g_Frame_Count:"+str(g_Frame_Count))
                    else:
                        my_logger.info("DB return null")
                        Retransmission_need_to_send = None
                except:
                    connection.rollback()
    finally:
        connection.close()

"""
Update which data should be change it's flag status, change g_Sended_Flag to 1 if the data has been sent, or change retransmit_flag to 0 if the retransmit data has been sent.
"""
def update_sensor_data_to_DB(db_type, l_sensor_macAddr, l_sensor_data, l_sensor_frameCnt):
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 #db='sensor',
                                 #charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            my_logger.info("connect to DB")
            try:
                cursor.execute("USE sensor")
            except:
                my_logger.info("No sensor DB")
            # update sensordata table
            if db_type == 1:
                my_logger.info("update sensordata table")
                if g_Sended_Flag ==0:
                    my_logger.info("update sensordata table g_Sended_Flag ==0")
                    sql = "update sensordata set sended_flag=1, last_sent_time=now() where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                elif g_Retransmit_Flag ==1:
                    my_logger.info("update sensordata table g_Retransmit_Flag ==1")
                    sql = "update sensordata set retransmit_flag=0, last_sent_time=now() where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            # update correctiontime table
            elif db_type == 2:
                my_logger.info("update correctiontime table")
                sql = "update correctiontime set sended_flag=1, last_sent_time=now() where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            # update retransmission table
            elif db_type == 3:
                my_logger.info("update retransmission table")
                sql = "update retransmission set sended_flag=1, last_sent_time=now() where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
    finally:
        connection.close()

"""
Delete data from database, delete the wrong data, for example: wrong data length or mac address not in ABP Group.
"""
def delete_data_to_DB(db_type, l_sensor_macAddr, l_sensor_data, l_sensor_frameCnt):
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 #db='sensor',
                                 #charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            my_logger.info("connect to DB")
            try:
                cursor.execute("USE sensor")
            except:
                my_logger.info("No sensor DB")
            # delete sensordata table
            if db_type == 1:
                my_logger.info("delete sensordata table")
                sql = "delete from sensordata where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            # delete correctiontime table
            elif db_type == 2:
                my_logger.info("delete correctiontime table")
                sql = "delete from correctiontime where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            # delete retransmission table
            elif db_type == 3:
                my_logger.info("delete retransmission table")
                sql = "delete from  retransmission where source_MAC_Address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
    finally:
        connection.close()

"""
Select the minimum frame counter from all three database, the minimum frame counter data should be sent first.
"""
def select_min_frame_count_from_DB():
    global g_minCnt
    global g_minCnt_tbl_name
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 #db='sensor',
                                 #charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            my_logger.info("connect to DB")
            try:
                cursor.execute("USE sensor")
            except:
                my_logger.info("No sensor DB")
            my_logger.info("select_min_frame_count_from_DB")
            # select minimum frame counter from all three tables
            try:
                sql="select min(frame_count) as minCnt, tbl_name from ((select sended_flag, frame_count, 0 as retransmit_flag, 'retransmission' as tbl_name from retransmission where sended_flag=0 ) union (select sended_flag, frame_count, 0 as retransmit_flag, 'correctiontime' as tbl_name from correctiontime where sended_flag=0) union (select sended_flag, frame_count, retransmit_flag, 'sensordata' as tbl_name from sensordata where sended_flag=0 or retransmit_flag=1)) as summaryTbl group by tbl_name limit 1"
                cursor.execute(sql)
                #connection.commit()
                #my_logger.info(cursor.rowcount)
                if(cursor.rowcount>0):
                    for row in cursor:
                        g_minCnt_tbl_name = row["tbl_name"]
                        g_minCnt = row["minCnt"]
                        my_logger.info("Select Table Name: "+str(g_minCnt_tbl_name))
                        my_logger.info("Min Counter: "+str(g_minCnt))
                else:
                    g_minCnt_tbl_name = None
                    g_minCnt = None
                    my_logger.info("select_min_frame_count_from_DB, DB return null")
            except:
                connection.rollback()
    finally:
        connection.close()

"""
Get MAC Address for serial interface by at command
"""
def get_lora_module_addr(dev_path):
    try:
        ser = serial.Serial(dev_path, 9600, timeout=0.5)
        ser.flushInput()
        ser.flushOutput()
        #ser.write("AT+cdevaddr=05002001\r\n")
        ser.write("AT+cdevaddr?\r\n")
        check_my_dongle = str(ser.readlines())
        #my_logger.info(check_my_dongle)
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
        #my_logger.info('My USB dongle checked')
        return ser
        #else:
            #return None
    except serial.serialutil.SerialException:
        # my_logger.info("FAIL: Cannot open Serial Port (No LoRa Node Inserted)")
        return None

"""
set SF and TXP
"""
def set_ATcomd_SF_TXP(ser):
    try:
        #print("Bill_Log:" + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        ser.write("AT+CADR=2,0,FFFF,0,1\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        ser.write("AT+CTXPS=1,0,7\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        #print("Bill_Log_OK" )
    except ValueError:
        my_logger.info("set_ATcomd_SF_TXP error")
        pass
"""
Main function will check the sock status in while loop. sock1: Diagnosis PC, sock2: Application Server, sock3: Microwave PC,
sock4: Radio(Not used) sock5: Display. And select the minimum frame counter from all three database then sent by lora at command.
"""
def main():
    global Data_need_to_send
    global Retransmission_need_to_send
    global Correction_Time_need_to_send
    global g_Sended_Flag
    global g_Retransmit_Flag
    global sock1
    global sock2
    global sock3
    global sock4
    global sock5
    global g_sock1_flag
    global g_sock2_flag
    global g_sock3_flag
    global g_sock4_flag
    global g_sock5_flag
    global g_socket_list
    global MAC_Address
    temp_Sended_Flag = -1

    build_app_group_table()

    my_logger.info("deq.py is started!")
    my_logger.info("dic - appskey and nwkskey")
    my_logger.info(my_dict_appskey)
    my_logger.info(my_dict_nwkskey)

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

    if global_check_dongle_exist is False:
        my_logger.info("no device be detected, exit!!!")
        sys.exit()

    my_dict = {}
    time_dict= {}

    while True:
        tmp = ""
        # check connect status
        if g_sock1_flag == -1:
            TCP_connect(Diagnosis_PC_ip_port)
            if g_sock1_flag == 0:
                ser.flushInput()
                ser.flushOutput()
                ser.write("at+dtx=11,\"1234567890a\"\r\n")
                #return_state = ser.readlines()
                #my_logger.info(return_state)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_DIAGNOSIS_IP + ':' + NETSTAT_DIAGNOSIS_PORT + '|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    my_logger.info("Diagnosis PC is disconnected by keep-alive timeout, so closing socket of Diagnosis PC")
                    g_sock1_flag = -1
                    close_socket(sock1)

            if g_sock1_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_DIAGNOSIS_IP + ':' + NETSTAT_DIAGNOSIS_PORT + '|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info("Diagnosis PC is disconnected by socket unknown, so closing socket of Diagnosis PC")
                        g_sock1_flag = -1
                        close_socket(sock1)

        # check connect status
        if g_sock2_flag == -1:
            TCP_connect(Application_Server_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_APPLICATION_IP + ':' + NETSTAT_APPLICATION_PORT + '|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    my_logger.info("Application Server is disconnected by keep-alive timeout, so closing socket of Application Server")
                    g_sock2_flag = -1
                    close_socket(sock2)

            if g_sock2_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_APPLICATION_IP + ':' +  NETSTAT_APPLICATION_PORT + '|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info("Application Server is disconnected by socket unknown, so closing socket of Application Server")
                        g_sock2_flag = -1
                        close_socket(sock2)

        # check connect status
        if g_sock3_flag == -1:
            TCP_connect(Microwave_PC_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_MICROWAVE_IP + ':' + NETSTAT_MICROWAVE_PORT + '|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    my_logger.info("Microwave PC is disconnected by keep-alive timeout, so closing socket of Microwave PC")
                    g_sock3_flag = -1
                    close_socket(sock3)

            if g_sock3_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_MICROWAVE_IP + ':' + NETSTAT_MICROWAVE_PORT + '|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info("Microwave PC is disconnected by socket unknown, so closing socket of Microwave PC")
                        g_sock3_flag = -1
                        close_socket(sock3)

        # check connect status
        if g_sock4_flag == -1:
            TCP_connect(Nport3_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_NPORT3_IP + ':' + NETSTAT_NPORT3_PORT + '|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock4_flag = -1
                    close_socket(sock4)
                    my_logger.info("NPort3 is disconnected by keep-alive timeout, so closing socket of NPort3")

            if g_sock4_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_NPORT3_IP + ':' + NETSTAT_NPORT3_PORT + '|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info("NPort3 is disconnected by socket unknown, so closing socket of NPort3")
                        g_sock4_flag = -1
                        close_socket(sock4)

        # check connect status
        if g_sock5_flag == -1:
            TCP_connect(Nport4_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_NPORT4_IP + ':' + NETSTAT_NPORT4_PORT + '|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    my_logger.info("NPort4 is disconnected by keep-alive timeout, so closing socket of NPort4")
                    g_sock5_flag = -1
                    close_socket(sock5)

            if g_sock5_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep ' + NETSTAT_NPORT4_IP + ':' + NETSTAT_NPORT4_PORT + '|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info("NPort4 is disconnected by socket unknown, so closing socket of NPort4")
                        g_sock5_flag = -1
                        close_socket(sock5)

        try:
            #Await a read event
            rlist, wlist, elist = select.select( g_socket_list, [], [], SELECT_TIMEOUT)
        except select.error:
            my_logger.info("select error")

        for sock in rlist:
            if sock1 == sock: # Diagnosis_PC
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock1 Diagnosis_PC disconnect")
                        g_sock1_flag = -1
                        close_socket(sock1)
                except socket.error:
                    my_logger.info("sock1 Diagnosis_PC socket recv error")
                    g_sock1_flag = -1
                    close_socket(sock1)
            elif sock2 == sock: # Application Server
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock2 Application Server disconnect")
                        g_sock2_flag = -1
                        close_socket(sock2)
                except socket.error:
                    my_logger.info("sock2 Application Server socket recv error")
                    g_sock2_flag = -1
                    close_socket(sock2)
            elif sock3 == sock: #Microwave PC
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock3 Microwave PC disconnect")
                        g_sock3_flag = -1
                        close_socket(sock3)
                except socket.error:
                    my_logger.info("sock3 Microwave PC socket recv error")
                    g_sock3_flag = -1
                    close_socket(sock3)
            elif sock4 == sock: # Radio(Not Used)
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock4 Radio disconnect")
                        g_sock4_flag = -1
                        close_socket(sock4)
                except socket.error:
                    my_logger.info("sock4 Radio socket recv error")
                    g_sock4_flag = -1
                    close_socket(sock4)
            elif sock5 == sock: # Display
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock5 Display disconnect")
                        g_sock5_flag = -1
                        close_socket(sock5)
                except socket.error:
                    my_logger.info("sock5 Display socket recv error")
                    g_sock5_flag = -1
                    close_socket(sock5)

        # select minimum frame counter from all three tables
        select_min_frame_count_from_DB()
        my_logger.info("g_minCnt_tbl_name:"+str(g_minCnt_tbl_name))
        if g_minCnt_tbl_name != None:
            if g_minCnt_tbl_name == 'sensordata':
                tablename = 'sensordata'
                get_sensor_data_from_DB(tablename)
            elif g_minCnt_tbl_name == 'correctiontime':
                tablename = 'correctiontime'
                get_sensor_data_from_DB(tablename)
            elif g_minCnt_tbl_name == 'retransmission':
                tablename = 'retransmission'
                get_sensor_data_from_DB(tablename)
        else:
            my_logger.info("No data need to be send")

        return_state = ""
        # check if there have sensordata need to send 
        if Data_need_to_send != None:
            my_logger.info("Sensor data send")
            #sensor_data = Data_need_to_send
            CMD = int(Data_need_to_send[0:2],16)
            tmp_data = Data_need_to_send[2:]
            recv_MAC_Level = CMD>>5
            if Self_MAC_Level != recv_MAC_Level:
                CMD = (Self_MAC_Level<<5) | (CMD & ~(1<<5 | 1<<6 | 1<<7))
            if g_Retransmit_Flag ==1:
                my_logger.info("g_Retransmit_Flag ==1 change command")
                CMD = (CMD & ~(1<<2)) | (CMD | 1<<3) | (CMD & ~(1<<4))
                my_logger.info("Retransmit CMD:"+str(CMD))
            cmd_hex_data = binascii.hexlify(struct.pack(Endian + 'B', CMD))
            sensor_data = str(cmd_hex_data)+tmp_data
            sensor_macAddr = Source_MAC_address
            sensor_data_len = len(sensor_data)
            sensor_frameCnt = g_Frame_Count
            my_logger.info("sensor_frameCnt:"+str(sensor_frameCnt))
            if (sensor_data_len %2) !=0 or sensor_data_len <18:
                length_flag=0
            else:
                length_flag=1
            if sensor_macAddr[0:2] in my_dict_appskey and length_flag==1:
                sensor_nwkskey = my_dict_nwkskey[sensor_macAddr[0:2]]
                sensor_appskey = my_dict_appskey[sensor_macAddr[0:2]]
                set_ATcomd_SF_TXP(ser)
                my_logger.info("sensor_data:"+str(sensor_data))
                data_sending = "AT+SSTX=" + str(sensor_data_len) + "," + sensor_data + "," + sensor_macAddr[0:8] + "," + str(sensor_frameCnt) + "," + sensor_nwkskey + "," + sensor_appskey + "\n"
                data_sending = str(data_sending)
                my_logger.info(data_sending)
                ser.flushInput()
                ser.flushOutput()
                ser.write(data_sending)
                time.sleep(MY_SLEEP_INTERVAL)
                return_state = ser.readlines()
                temp_Sended_Flag = g_Sended_Flag
                #my_logger.info(return_state)
            # group error or length error
            else:
                if length_flag ==0:
                    my_logger.info("Data length error, should not be odd or sensordata length less then 18!")
                    delete_data_to_DB(1, sensor_macAddr, Data_need_to_send, sensor_frameCnt);
                else:
                    my_logger.info("Not in ABP Group Config Rule, so give up")
                    delete_data_to_DB(1, sensor_macAddr, Data_need_to_send, sensor_frameCnt);
                    length_flag=0 #set flag=0 not show display

            if SENT_OK_TAG in return_state:
                my_logger.info("Result: SENT.")
            else:
                my_logger.info("Result: Send FAIL!")

            #sended than update DB change sended flag to 1 by nick
            update_sensor_data_to_DB(1, sensor_macAddr, Data_need_to_send, sensor_frameCnt);
            Data_need_to_send = None

            #Send sensor data to application server or Microwave PC or Radio(Not uesd)
            try:
                my_logger.info("Send sensor data to Application Server")
                socket_string = str(sensor_macAddr+sensor_data)
                socket_bytes = bytearray.fromhex(socket_string)
                sock2.send(socket_bytes)
            except socket.error:
                my_logger.info("sock2 Application Server socket send error")
                g_sock2_flag = -1
                close_socket(sock2)
            try:
                my_logger.info("Send sensor data to Microwave PC")
                socket_string = str(sensor_macAddr+sensor_data)
                socket_bytes = bytearray.fromhex(socket_string)
                sock3.send(socket_bytes)
            except socket.error:
                my_logger.info("sock3 Microwave PC socket send error")
                g_sock3_flag = -1
                close_socket(sock3)
            try:
                my_logger.info("Send sensor data to Radio")
                socket_string = str(sensor_macAddr+sensor_data)
                socket_bytes = bytearray.fromhex(socket_string)
                sock4.send(socket_bytes)
            except socket.error:
                my_logger.info("sock4 Radio socket send error")
                g_sock4_flag = -1
                close_socket(sock4)

            # Send sensor data to Display
            if MAC_Address == sensor_macAddr[0:8] and length_flag == 1 and temp_Sended_Flag == 0:
                try:
                    my_logger.info("Send sensor data to Display")
                    # convert from dec to hex
                    combinestr = str(int(sensor_data[10:14],16))+str(int(sensor_data[14:16],16)).zfill(2)
                    my_logger.info("combinestr:"+str(combinestr))
                    if int(combinestr) > 65535:
                        convertdata = str('{0:X}'.format(int(combinestr))).zfill(6)
                        my_logger.info("convertdata:"+str(convertdata))
                        crc_data = unhexlify('00060027'+str(convertdata[2:6]))
                    else:
                        convertdata = str('{0:X}'.format(int(combinestr))).zfill(4)
                        my_logger.info("convertdata:"+str(convertdata))
                        crc_data = unhexlify('00060027'+str(convertdata))
                    # calc crc
                    crc_func = crcmod.predefined.mkCrcFun('modbus')
                    modbus_crc = str('{0:X}'.format(crc_func(crc_data))).zfill(4)
                    my_logger.info("Modbus CRC:"+str(modbus_crc))
                    low_crc = str(modbus_crc)[2:4]
                    high_crc = str(modbus_crc)[0:2]
                    # display high byte(0026 reg) low byte (0027 reg)
                    # e.g 0006(cmd)0026(reg)0001(value) A810(modbus RTU crc)
                    if len(convertdata) >4:
                        my_logger.info("Display Data > 65535")
                        socksend_high_data = unhexlify('000600260001A810')
                        sock5.send(socksend_high_data)
                        time.sleep(1)
                        socksend_low_data = unhexlify('00060027'+convertdata[2:6]+low_crc+high_crc)
                        sock5.send(socksend_low_data)
                    else:
                        my_logger.info("Display Data <= 65535")
                        socksend_high_data = unhexlify('00060026000069D0')
                        sock5.send(socksend_high_data)
                        time.sleep(1)
                        socksend_low_data = unhexlify('00060027'+convertdata+low_crc+high_crc)
                        sock5.send(socksend_low_data)
                except socket.error:
                    my_logger.info("sock5 Display socket error 2")
                    g_sock5_flag = -1
                    close_socket(sock5)
        else:
            my_logger.info("Waiting for incoming queue")

        return_state = ""
        # check if there have Correction time data need to send
        if Correction_Time_need_to_send != None:
            my_logger.info("Correction time send")
            #convert Correction_Time_need_to_send to hex time
            #sensor_data = Correction_Time_need_to_send
            CMD = int(Correction_Time_need_to_send[0:2],16)
            tmp_data = Correction_Time_need_to_send[2:]
            recv_MAC_Level = CMD>>5
            my_logger.info("recv_MAC_Level:"+str(recv_MAC_Level))
            if Self_MAC_Level != recv_MAC_Level:
                CMD = (Self_MAC_Level<<5) | (CMD & ~(1<<5 | 1<<6 | 1<<7))
            cmd_hex_data = binascii.hexlify(struct.pack(Endian + 'B', CMD))
            sensor_data = str(cmd_hex_data)+tmp_data
            sensor_macAddr = Source_MAC_address
            sensor_data_len = len(sensor_data)
            sensor_frameCnt = g_Frame_Count
            my_logger.info("sensor_frameCnt:"+str(sensor_frameCnt))
            if (sensor_data_len %2) !=0:
                length_flag=0
            else:
                length_flag=1
            if sensor_macAddr[0:2] in my_dict_appskey:
                sensor_nwkskey = my_dict_nwkskey[sensor_macAddr[0:2]]
                sensor_appskey = my_dict_appskey[sensor_macAddr[0:2]]
                set_ATcomd_SF_TXP(ser)
                my_logger.info("sensor_data:"+str(sensor_data))
                data_sending = "AT+SSTX=" + str(sensor_data_len) + "," + sensor_data + "," + sensor_macAddr[0:8] + "," + str(sensor_frameCnt) + "," + sensor_nwkskey + "," + sensor_appskey + "\n"
                data_sending = str(data_sending)
                my_logger.info(data_sending)
                #update DB sended flag here when sended and return status = "tx done        " bu nick
                ser.flushInput()
                ser.flushOutput()
                ser.write(data_sending)
                time.sleep(MY_SLEEP_INTERVAL)
                return_state = ser.readlines()
                #my_logger.info(return_state)
            # group error or length error
            else:
                if length_flag ==0:
                    my_logger.info("Data length error, should not be odd!")
                    delete_data_to_DB(1, sensor_macAddr, Correction_Time_need_to_send, sensor_frameCnt);
                else:
                    my_logger.info("Not in ABP Group Config Rule, so give up")
                    delete_data_to_DB(2, sensor_macAddr, Correction_Time_need_to_send, sensor_frameCnt);

            if SENT_OK_TAG in return_state:
                my_logger.info("Result: SENT.")
            else:
                my_logger.info("Result: Send FAIL!")

            #sended than update DB change sended flag to 1 by nick
            update_sensor_data_to_DB(2, sensor_macAddr, Correction_Time_need_to_send, sensor_frameCnt);
            Correction_Time_need_to_send = None

            # FFFFFF is broad cast packet
            if 'ffffff' not in sensor_macAddr and 'FFFFFF' not in sensor_macAddr:
                #Send correctiontime ACK to application server or Microwave PC or Radio
                try:
                    my_logger.info("Send correctiontime ACK to Application Server")
                    socket_string = str(sensor_macAddr+sensor_data)
                    socket_bytes = bytearray.fromhex(socket_string)
                    sock2.send(socket_bytes)
                except socket.error:
                    my_logger.info("sock2 Application Server socket send ACK error")
                    g_sock2_flag = -1
                    close_socket(sock2)
                try:
                    my_logger.info("Send correctiontime ACK to Microwave PC")
                    socket_string = str(sensor_macAddr+sensor_data)
                    socket_bytes = bytearray.fromhex(socket_string)
                    sock3.send(socket_bytes)
                except socket.error:
                    my_logger.info("sock3 Microwave PC socket send ACK error")
                    g_sock3_flag = -1
                    close_socket(sock3)
                try:
                    my_logger.info("Send correctiontime ACK to Radio")
                    socket_string = str(sensor_macAddr+sensor_data)
                    socket_bytes = bytearray.fromhex(socket_string)
                    sock4.send(socket_bytes)
                except socket.error:
                    my_logger.info("sock4 Radio socket send ACK error")
                    g_sock4_flag = -1
                    close_socket(sock4)

        return_state = ""
        # check if there have Retransmit data need to send
        if Retransmission_need_to_send != None:
            my_logger.info("Retransmit send")
            sensor_data = Retransmission_need_to_send
            CMD = int(Retransmission_need_to_send[0:2],16)
            tmp_data = Retransmission_need_to_send[2:]
            recv_MAC_Level = CMD>>5
            if Self_MAC_Level != recv_MAC_Level:
                CMD = (Self_MAC_Level<<5) | (CMD & ~(1<<5 | 1<<6 | 1<<7))
            cmd_hex_data = binascii.hexlify(struct.pack(Endian + 'B', CMD))
            sensor_data = str(cmd_hex_data)+tmp_data
            sensor_macAddr = Source_MAC_address
            sensor_data_len = len(sensor_data)
            sensor_frameCnt = g_Frame_Count
            my_logger.info("sensor_frameCnt:"+str(sensor_frameCnt))
            if (sensor_data_len %2) !=0:
                length_flag=0
            else:
                length_flag=1
            if sensor_macAddr[0:2] in my_dict_appskey:
                sensor_nwkskey = my_dict_nwkskey[sensor_macAddr[0:2]]
                sensor_appskey = my_dict_appskey[sensor_macAddr[0:2]]
                set_ATcomd_SF_TXP(ser)
                my_logger.info("sensor_data:"+str(sensor_data))
                data_sending = "AT+SSTX=" + str(sensor_data_len) + "," + sensor_data + "," + sensor_macAddr[0:8] + "," + str(sensor_frameCnt) + "," + sensor_nwkskey + "," + sensor_appskey + "\n"
                data_sending = str(data_sending)
                my_logger.info(data_sending)
                ser.flushInput()
                ser.flushOutput()
                ser.write(data_sending)
                time.sleep(MY_SLEEP_INTERVAL)
                return_state = ser.readlines()
                #my_logger.info(return_state)
            # group error or length error
            else:
                if length_flag ==0:
                    my_logger.info("Data length error, should not be odd!")
                    delete_data_to_DB(3, sensor_macAddr, Retransmission_need_to_send, sensor_frameCnt);
                else:
                    my_logger.info("Not in ABP Group Config Rule, so give up")
                    delete_data_to_DB(3, sensor_macAddr, Retransmission_need_to_send, sensor_frameCnt);

            if SENT_OK_TAG in return_state:
                my_logger.info("Result: SENT.")
            else:
                my_logger.info("Result: Send FAIL!")

            #sended than update DB change sended flag to 1 by nick
            update_sensor_data_to_DB(3, sensor_macAddr, Retransmission_need_to_send, sensor_frameCnt);
            Retransmission_need_to_send = None

        #To send LoRa repeater I/O status to  Diagnosis PC
        if g_sock1_flag == 0:
            report_status_to_diagnosis_pc()

if __name__ == "__main__":
    main()
