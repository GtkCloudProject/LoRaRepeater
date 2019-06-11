#!/usr/bin/python

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

Nport1_ip_port = ('192.168.127.88',4001) #water meter
Nport2_ip_port = ('192.168.127.88',4002) #rain meter
Nport3_ip_port = ('192.168.127.88',4003) #radio
Nport4_ip_port = ('192.168.127.88',4004) #display
Diagnosis_PC_ip_port = ('192.168.127.99',4005)
Application_Server_ip_port = ('192.168.127.101',4006)
Microwave_PC_ip_port = ('192.168.127.102',4007)

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

#To close socket
def close_socket(sock_c):
    global g_socket_list

    sock_c.close()
    try:
        g_socket_list.remove(sock_c)
    except ValueError:
        pass

#To show device I/O status
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

    try:
        my_logger.info("Send sensor data to Diagnosis PC")
        sock1.send("== I/O Status Reporting ==\n")
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

#add by nick
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

#add by nick
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

#add by nick
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
            elif db_type == 2:
                my_logger.info("update correctiontime table")
                sql = "update correctiontime set sended_flag=1, last_sent_time=now() where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            elif db_type == 3:
                my_logger.info("update retransmission table")
                sql = "update retransmission set sended_flag=1, last_sent_time=now() where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
    finally:
        connection.close()
#add by nick
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
            if db_type == 1:
                my_logger.info("delete sensordata table")
                sql = "delete from sensordata where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            elif db_type == 2:
                my_logger.info("delete correctiontime table")
                sql = "delete from correctiontime where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            elif db_type == 3:
                my_logger.info("delete retransmission table")
                sql = "delete from  retransmission where source_MAC_Address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
    finally:
        connection.close()

#add by nick
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

#get MAC Address for serial
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
        if g_sock1_flag == -1:
            TCP_connect(Diagnosis_PC_ip_port)
            if g_sock1_flag == 0:
                ser.flushInput()
                ser.flushOutput()
                ser.write("at+dtx=11,\"1234567890a\"\r\n")
                #return_state = ser.readlines()
                #my_logger.info(return_state)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.99:4005|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock1_flag = -1
                    close_socket(sock1)
            if g_sock1_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.99:4005|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info(res_return)
                        g_sock1_flag = -1
                        close_socket(sock1)

        if g_sock2_flag == -1:
            TCP_connect(Application_Server_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.101:4006|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock2_flag = -1
                    close_socket(sock2)
            if g_sock2_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.101:4006|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info(res_return)
                        g_sock2_flag = -1
                        close_socket(sock2)

        if g_sock3_flag == -1:
            TCP_connect(Microwave_PC_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.102:4007|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock3_flag = -1
                    close_socket(sock3)
            if g_sock3_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.102:4007|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info(res_return)
                        g_sock3_flag = -1
                        close_socket(sock3)

        if g_sock4_flag == -1:
            TCP_connect(Nport3_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.88:4003|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock4_flag = -1
                    close_socket(sock4)
            if g_sock4_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.88:4003|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info(res_return)
                        g_sock4_flag = -1
                        close_socket(sock4)

        if g_sock5_flag == -1:
            TCP_connect(Nport4_ip_port)
        else:
            cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.88:4004|awk -F \"/\" \'{print $(NF-1)}\'').readlines()
            count1 = 0
            for count1 in range(len(cmd_res)):
                if int(cmd_res[count1]) > 0:
                    g_sock5_flag = -1
                    close_socket(sock5)
            if g_sock5_flag == 0:
                cmd_res = os.popen('netstat -apn --timer|grep 192.168.127.88:4004|awk \'{print $8}\'').readlines()
                count1 = 0
                for count1 in range(len(cmd_res)):
                    res_return = cmd_res[count1].find(SOCK_UNKNOW)
                    if int(res_return) != -1:
                        my_logger.info(res_return)
                        g_sock5_flag = -1
                        close_socket(sock5)

        try:
            #Await a read event
            rlist, wlist, elist = select.select( g_socket_list, [], [], SELECT_TIMEOUT)
        except select.error:
            my_logger.info("select error")

        for sock in rlist:
            if sock1 == sock: #Diagnosis_PC
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock1 Diagnosis_PC disconnect")
                        g_sock1_flag = -1
                        close_socket(sock1)
                except socket.error:
                    my_logger.info("sock1 Diagnosis_PC socket error")
                    g_sock1_flag = -1
                    close_socket(sock1)
            elif sock2 == sock: #Application Server
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock2 Application Server disconnect")
                        g_sock2_flag = -1
                        close_socket(sock2)
                except socket.error:
                    my_logger.info("sock2 Application Server socket error")
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
                    my_logger.info("sock3 Microwave PC socket error")
                    g_sock3_flag = -1
                    close_socket(sock3)
            elif sock4 == sock: #Radio
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock4 Radio disconnect")
                        g_sock4_flag = -1
                        close_socket(sock4)
                except socket.error:
                    my_logger.info("sock4 Radio socket error")
                    g_sock4_flag = -1
                    close_socket(sock4)
            elif sock5 == sock: #Display
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        my_logger.info("sock5 Display disconnect")
                        g_sock5_flag = -1
                        close_socket(sock5)
                except socket.error:
                    my_logger.info("sock5 Display socket error 1")
                    g_sock5_flag = -1
                    close_socket(sock5)

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
                #sended than update DB change sended flag to 1 by nick
                update_sensor_data_to_DB(1, sensor_macAddr, Data_need_to_send, sensor_frameCnt);
                Data_need_to_send = None
                sent_flag=1
            else:
                my_logger.info("Result: Send FAIL!")
                sent_flag=0
            #Send sensor data to application server or Microwave PC or Radio
            if sent_flag==1:
                try:
                    my_logger.info("Send sensor data to Application Server")
                    sock2.send(sensor_macAddr+sensor_data)
                except socket.error:
                    my_logger.info("sock2 Application Server socket error")
                    g_sock2_flag = -1
                    close_socket(sock2)
                try:
                    my_logger.info("Send sensor data to Microwave PC")
                    sock3.send(sensor_macAddr+sensor_data)
                except socket.error:
                    my_logger.info("sock3 Microwave PC socket error")
                    g_sock3_flag = -1
                    close_socket(sock3)
                try:
                    sended_len = sock4.send(sensor_macAddr+sensor_data)
                    my_logger.info("Send sensor data to Radio")
                except socket.error:
                    my_logger.info("sock4 Radio socket error")
                    g_sock4_flag = -1
                    close_socket(sock4)
            if Self_MAC_Level == recv_MAC_Level and length_flag==1:
                try:
                    my_logger.info("Send sensor data to Display")
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
                    crc_func = crcmod.predefined.mkCrcFun('modbus')
                    modbus_crc = str('{0:X}'.format(crc_func(crc_data))).zfill(4)
                    my_logger.info("Modbus CRC:"+str(modbus_crc))
                    low_crc = str(modbus_crc)[2:4]
                    high_crc = str(modbus_crc)[0:2]
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
            else:
                if length_flag ==0:
                    my_logger.info("Data length error, should not be odd!")
                    delete_data_to_DB(1, sensor_macAddr, Correction_Time_need_to_send, sensor_frameCnt);
                else:
                    my_logger.info("Not in ABP Group Config Rule, so give up")
                    delete_data_to_DB(2, sensor_macAddr, Correction_Time_need_to_send, sensor_frameCnt);

            if SENT_OK_TAG in return_state:
                my_logger.info("Result: SENT.")
                #sended than update DB change sended flag to 1 by nick
                update_sensor_data_to_DB(2, sensor_macAddr, Correction_Time_need_to_send, sensor_frameCnt);
                Correction_Time_need_to_send = None
                sent_flag=1
            else:
                my_logger.info("Result: Send FAIL!")
                sent_flag=0

            if 'ffffff' not in sensor_macAddr and 'FFFFFF' not in sensor_macAddr and sent_flag==1:
                #Send correctiontime ACK to application server or Microwave PC or Radio
                try:
                    my_logger.info("Send correctiontime ACK to Application Server")
                    sock2.send(sensor_macAddr+sensor_data)
                except socket.error:
                    my_logger.info("sock2 Application Server socket error")
                    g_sock2_flag = -1
                    close_socket(sock2)
                try:
                    my_logger.info("Send correctiontime ACK to Microwave PC")
                    sock3.send(sensor_macAddr+sensor_data)
                except socket.error:
                    my_logger.info("sock3 Microwave PC socket error")
                    g_sock3_flag = -1
                    close_socket(sock3)
                try:
                    my_logger.info("Send correctiontime ACK to Radio")
                    sock4.send(sensor_macAddr+sensor_data)
                except socket.error:
                    my_logger.info("sock4 Radio socket error")
                    g_sock4_flag = -1
                    close_socket(sock4)

        return_state = ""
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
            else:
                if length_flag ==0:
                    my_logger.info("Data length error, should not be odd!")
                    delete_data_to_DB(3, sensor_macAddr, Retransmission_need_to_send, sensor_frameCnt);
                else:
                    my_logger.info("Not in ABP Group Config Rule, so give up")
                    delete_data_to_DB(3, sensor_macAddr, Retransmission_need_to_send, sensor_frameCnt);

            if SENT_OK_TAG in return_state:
                my_logger.info("Result: SENT.")
                #sended than update DB change sended flag to 1 by nick
                update_sensor_data_to_DB(3, sensor_macAddr, Retransmission_need_to_send, sensor_frameCnt);
                Retransmission_need_to_send = None
                sent_flag=1
            else:
                my_logger.info("Result: Send FAIL!")
                sent_flag=0

        #To send LoRa repeater I/O status to  Diagnosis PC
        if g_sock1_flag == 0:
            report_status_to_diagnosis_pc()

if __name__ == "__main__":
    main()
