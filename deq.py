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

MY_SLEEP_INTERVAL = 3.5
MY_ALIVE_INTERVAL = 86400

MY_MQTT_QUEUE_FILE_PATH = "/var/lora_repeater/queue/"
MY_SENDING_FILE_PATH = "/var/lora_repeater/sending/"
MY_SENT_FILE_PATH = "/var/lora_repeater/sent/"
MY_SEND_FAIL_FILE_PATH = "/var/lora_repeater/fail/"
MY_LOG_FILE_PATH = "/var/lora_repeater/log/"

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
g_Frame_Count = ""
g_Sended_Flag = ""
g_Retransmit_Flag = ""
Source_MAC_address = ""

Nport1_ip_port = ('192.168.127.88',4001) #water meter
Nport2_ip_port = ('192.168.127.88',4002) #rain meter
Nport3_ip_port = ('192.168.127.88',4003) #radio
Nport4_ip_port = ('192.168.127.88',4004) #display
Diagnosis_PC_ip_port = ('192.168.127.99',4005)
Application_Server_ip_port = ('192.168.127.101',4006)
Microwave_PC_ip_port = ('192.168.127.102',4007)

my_dict_appskey = {}
my_dict_nwkskey = {}

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
        print("Send sensor data to Diagnosis PC")
        sock1.send("== I/O Status Reporting ==\n")

        # LoRa
        sub_p = subprocess.Popen("cat /tmp/lora_status", stdout=subprocess.PIPE, shell=True)
        (lora_status, err) = sub_p.communicate()
        if len(lora_status) > 0:
            lora_status = int(lora_status)
        else:
            lora_status = -1

        if lora_status == 0:
            io_status = "LoRa Status %s \n" %(STATUS_OK)
            print(io_status)
            sock1.send(io_status)
        else:
            io_status = "LoRa Status %s \n" %(STATUS_FAIL)
            print(io_status)
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
            print(io_status)
            sock1.send(io_status)
        else:
            io_status = "N Port Port 1 Status %s \n" %(STATUS_FAIL)
            print(io_status)
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
            print(io_status)
            sock1.send(io_status)
        else:
            io_status = "N Port Port 2 Status %s \n" %(STATUS_FAIL)
            print(io_status)
            sock1.send(io_status)

        # N port port 3
        if g_Nport3_ip_port_status == 0:
            io_status = "N Port Port 3 Status %s \n" %(STATUS_OK)
            print(io_status)
            sock1.send(io_status)
        else:
            io_status = "N Port Port 3 Status %s \n" %(STATUS_FAIL)
            print(io_status)
            sock1.send(io_status)

        # N port port 4
        if g_Nport4_ip_port_status == 0:
            io_status = "N Port Port 4 Status %s \n" %(STATUS_OK)
            print(io_status)
            sock1.send(io_status)
        else:
            io_status = "N Port Port 4 Status %s \n" %(STATUS_FAIL)
            print(io_status)
            sock1.send(io_status)

        #Application Server
        if g_Application_Server_ip_port_status == 0:
            io_status = "Application_Server Status %s \n" %(STATUS_OK)
            print(io_status)
            sock1.send(io_status)
        else:
            io_status = "Application_Server Status %s \n" %(STATUS_FAIL)
            print(io_status)
            sock1.send(io_status)

        #Microwave_PC
        if g_Microwave_PC_ip_port_status == 0:
            io_status = "Microwave PC Status %s \n" %(STATUS_OK)
            print(io_status)
            sock1.send(io_status)
        else:
            io_status = "Microwave PC Status %s \n" %(STATUS_FAIL)
            print(io_status)
            sock1.send(io_status)

        sock1.send("\n")

    except socket.error:
        print"sock1 Diagnosis_PC socket error"
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
            print "sock1 Diagnosis PC connect"
            g_sock1_flag = 0
            g_socket_list.append(sock1)
        except:
            print "sock1 Diagnosis PC connect error"
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
            print "sock2 Application Server connect"
            g_Application_Server_ip_port_status = 0
            g_sock2_flag = 0
            g_socket_list.append(sock2)
        except:
            print"sock2 Application Server connect error"
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
            print "sock3 Microwave PC connect"
            g_Microwave_PC_ip_port_status = 0
            g_sock3_flag = 0
            g_socket_list.append(sock3)
        except:
            print"sock3 Microwave PC connect error"
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
            print "sock4 Radio connect"
            g_Nport3_ip_port_status = 0
            g_sock4_flag = 0
            g_socket_list.append(sock4)
        except:
            print"sock4 Radio connect error"
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
            print "sock5 Display connect"
            g_Nport4_ip_port_status = 0
            g_sock5_flag = 0
            g_socket_list.append(sock5)
        except:
            print"sock5 Display connect error"
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
            print("connect to DB")
            try:
                cursor.execute("USE sensor")
            except:
                connection.rollback()
                print("No sensor DB")
            global Source_MAC_address
            global Retransmission_need_to_send
            global g_Frame_Count
            global g_Sended_Flag
            global g_Retransmit_Flag
            global Data_need_to_send
            global Correction_Time_need_to_send
            if tablename == 'sensordata':
                print "tablename == sensordata"
                try:
                    sql = "select sended_flag, retransmit_flag, raw_data, source_mac_address, frame_count from sensordata WHERE sended_flag='0' or retransmit_flag='1' limit 1"
                    cursor.execute(sql)
                    #print cursor.rowcount
                    if(cursor.rowcount>0):
                        for row in cursor:
                            Data_need_to_send = row["raw_data"]
                            Source_MAC_address = row["source_mac_address"]
                            g_Frame_Count = row["frame_count"]
                            g_Sended_Flag = row["sended_flag"]
                            g_Retransmit_Flag = row["retransmit_flag"]
                            print "Source_MAC_address: " ,Source_MAC_address
                            print "Data_need_to_send: ",Data_need_to_send
                            print "Frame Count:", g_Frame_Count
                            print "g_Sended_Flag:", g_Sended_Flag
                            print "g_Retransmit_Flag:", g_Retransmit_Flag
                    else:
                        print "DB return null"
                        Data_need_to_send = None
                except:
                    connection.rollback()
            elif tablename == 'correctiontime':
                print "tablename == correctiontime"
                try:
                    sql = "select source_mac_address, sended_flag, raw_data, frame_count from correctiontime WHERE sended_flag='0' limit 1"
                    cursor.execute(sql)
                    #print cursor.rowcount
                    if(cursor.rowcount>0):
                        for row in cursor:
                            Correction_Time_need_to_send = row["raw_data"]
                            g_Frame_Count = row["frame_count"]
                            Source_MAC_address = row["source_mac_address"]
                            print "Correction_Time_need_to_send: ",Correction_Time_need_to_send
                            print "Frame Count:", g_Frame_Count
                            print "Source_MAC_address: " ,Source_MAC_address
                    else:
                        print "DB return null"
                        Correction_Time_need_to_send = None
                except:
                    print "Correction_Time table except"
                    connection.rollback()
            elif tablename == 'retransmission':
                print "tablename == retransmission"
                try:
                    sql = "select source_mac_address, sended_flag, raw_data, source_mac_address, frame_count from retransmission WHERE sended_flag='0' limit 1"
                    cursor.execute(sql)
                    #print cursor.rowcount
                    if(cursor.rowcount>0):
                        for row in cursor:
                            Retransmission_need_to_send = row["raw_data"]
                            Source_MAC_address = row["source_mac_address"]
                            g_Frame_Count = row["frame_count"]
                            print "Source_MAC_address: " ,Source_MAC_address
                            print "Retransmission_need_to_send: ",Retransmission_need_to_send
                            print "Frame Count:", g_Frame_Count
                    else:
                        print "DB return null"
                        Retransmission_need_to_send = None
                except:
                    connection.rollback()
    finally:
        connection.close()

#add by nick
def update_sensor_data_to_DB(type, l_sensor_macAddr, l_sensor_data, l_sensor_frameCnt):
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 #db='sensor',
                                 #charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            print("connect to DB")
            try:
                cursor.execute("USE sensor")
            except:
                print("No sensor DB")
            if type == 1:
                print("update sensordata table")
                if g_Sended_Flag ==0:
                    print("update sensordata table g_Sended_Flag ==0")
                    sql = "update sensordata set sended_flag=1 where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                elif g_Retransmit_Flag ==1:
                    print("update sensordata table g_Retransmit_Flag ==1")
                    sql = "update sensordata set retransmit_flag=0 where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            elif type == 2:
                print("update correctiontime table")
                sql = "update correctiontime set sended_flag=1 where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
            elif type == 3:
                print("update retransmission table")
                sql = "update retransmission set sended_flag=1 where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
                cursor.execute(sql)
                connection.commit()
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
    my_logger = logging.getLogger('dequeue')
    # Add the log message handler to the logger
    my_logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(MY_LOG_FILENAME, maxBytes=10240, backupCount=100)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
    my_logger.info('I am started!')

    build_app_group_table()

    print('deq.py is started!')
    print('dic - appskey and nwkskey')
    print(my_dict_appskey)
    print(my_dict_nwkskey)

    # example
    # my_logger.debug('debug message')
    # my_logger.info('info message')
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

    if global_check_dongle_exist is False:
        print('no device be detected, exit!!!')
        sys.exit()

    my_dict = {}
    time_dict= {}

    while True:
        if g_sock1_flag == -1:
            TCP_connect(Diagnosis_PC_ip_port)
            if g_sock1_flag == 0:
                ser.flushInput()
                ser.flushOutput()
                ser.write("at+dtx=11,\"1234567890a\"\r\n")
                #return_state = ser.readlines()
                #print(return_state)
        if g_sock2_flag == -1:
            TCP_connect(Application_Server_ip_port)
        if g_sock3_flag == -1:
            TCP_connect(Microwave_PC_ip_port)
        if g_sock4_flag == -1:
            TCP_connect(Nport3_ip_port)
        if g_sock5_flag == -1:
            TCP_connect(Nport4_ip_port)

        try:
            #Await a read event
            rlist, wlist, elist = select.select( g_socket_list, [], [], SELECT_TIMEOUT)
        except select.error:
            print "select error"

        for sock in rlist:
            if sock1 == sock: #Diagnosis_PC
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        print "sock1 Diagnosis_PC disconnect"
                        g_sock1_flag = -1
                        close_socket(sock1)
                except socket.error:
                    print "sock1 Diagnosis_PC socket error"
                    g_sock1_flag = -1
                    close_socket(sock1)
            elif sock2 == sock: #Application Server
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        print "sock2 Application Server disconnect"
                        g_sock2_flag = -1
                        close_socket(sock2)
                except socket.error:
                    print "sock2 Application Server socket error"
                    g_sock2_flag = -1
                    close_socket(sock2)
            elif sock3 == sock: #Microwave PC
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        print "sock3 Microwave PC disconnect"
                        g_sock3_flag = -1
                        close_socket(sock3)
                except socket.error:
                    print "sock3 Microwave PC socket error"
                    g_sock3_flag = -1
                    close_socket(sock3)
            elif sock4 == sock: #Radio
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        print "sock4 Radio disconnect"
                        g_sock4_flag = -1
                        close_socket(sock4)
                except socket.error:
                    print "sock4 Radio socket error"
                    g_sock4_flag = -1
                    close_socket(sock4)
            elif sock5 == sock: #Display
                try:
                    recvdata = sock.recv(1024)
                    if not recvdata:
                        print "sock5 Display disconnect"
                        g_sock5_flag = -1
                        close_socket(sock5)
                except socket.error:
                    print "sock5 Display socket error"
                    g_sock5_flag = -1
                    close_socket(sock5)

        tablename = 'sensordata'
        get_sensor_data_from_DB(tablename)
        return_state = ""
        if Data_need_to_send != None:
            print "Sensor data send"
            #sensor_data = Data_need_to_send
            CMD = int(Data_need_to_send[0:2],16)
            tmp_data = Data_need_to_send[2:]
            recv_MAC_Level = CMD>>5
            if Self_MAC_Level != recv_MAC_Level:
                CMD = (Self_MAC_Level<<5) | (CMD & ~(1<<5 | 1<<6 | 1<<7))
            if g_Retransmit_Flag ==1:
                print "g_Retransmit_Flag ==1 change command"
                CMD = (CMD & ~(1<<2)) | (CMD | 1<<3) | (CMD & ~(1<<4))
                print "Retransmit CMD:",CMD
            cmd_hex_data = binascii.hexlify(struct.pack(Endian + 'B', CMD))
            sensor_data = str(cmd_hex_data)+tmp_data
            sensor_macAddr = Source_MAC_address
            sensor_data_len = len(sensor_data)
            sensor_frameCnt = g_Frame_Count
            if sensor_macAddr[0:2] in my_dict_appskey:
                sensor_nwkskey = my_dict_nwkskey[sensor_macAddr[0:2]]
                sensor_appskey = my_dict_appskey[sensor_macAddr[0:2]]
                print("sensor_data:" + sensor_data )
                data_sending = "AT+SSTX=" + str(sensor_data_len) + "," + sensor_data + "," + sensor_macAddr[0:8] + "," + sensor_frameCnt + "," + sensor_nwkskey + "," + sensor_appskey + "\n"
                data_sending = str(data_sending)
                print data_sending
                ser.flushInput()
                ser.flushOutput()
                ser.write(data_sending)
                time.sleep(MY_SLEEP_INTERVAL)
                return_state = ser.readlines()
                #print(return_state)
            else:
                print('Not in ABP Group Config Rule, so give up')
                update_sensor_data_to_DB(1, sensor_macAddr, Data_need_to_send, sensor_frameCnt);

            if SENT_OK_TAG in return_state:
                print("Result: SENT.")
                #sended than update DB change sended flag to 1 by nick
                update_sensor_data_to_DB(1, sensor_macAddr, Data_need_to_send, sensor_frameCnt);
                Data_need_to_send = None
            else:
                print("Result: Send FAIL!")
            #Send sensor data to application server or Microwave PC or Radio
            try:
                print("Send sensor data to Application Server")
                sock2.send(sensor_macAddr+sensor_data)
            except socket.error:
                print"sock2 Application Server socket error"
                TCP_connect(Application_Server_ip_port)
            try:
                print("Send sensor data to Microwave PC")
                sock3.send(sensor_macAddr+sensor_data)
            except socket.error:
                print"sock3 Microwave PC socket error"
                TCP_connect(Microwave_PC_ip_port)
            try:
                print("Send sensor data to Radio")
                sock4.send(sensor_macAddr+sensor_data)
            except socket.error:
                print"sock4 Radio socket error"
                TCP_connect(Nport3_ip_port)
            if Self_MAC_Level == recv_MAC_Level:
                try:
                    print("Send sensor data to Display")
                    combinestr = str(int(sensor_data[10:14],16))+str(int(sensor_data[14:16],16)).zfill(2)
                    print "combinestr:",combinestr
                    if int(combinestr) > 65535:
                        convertdata = str('{0:X}'.format(int(combinestr))).zfill(6)
                        print "convertdata:",convertdata
                        crc_data = unhexlify('00060027'+str(convertdata[2:6]))
                    else:
                        convertdata = str('{0:X}'.format(int(combinestr))).zfill(4)
                        print "convertdata:",convertdata
                        crc_data = unhexlify('00060027'+str(convertdata))
                    crc_func = crcmod.predefined.mkCrcFun('modbus')
                    modbus_crc = str('{0:X}'.format(crc_func(crc_data))).zfill(4)
                    print "Modbus CRC:",modbus_crc
                    low_crc = str(modbus_crc)[2:4]
                    high_crc = str(modbus_crc)[0:2]
                    if len(convertdata) >4:
                        print "Display Data > 65535"
                        socksend_high_data = unhexlify('000600260001A810')
                        sock5.send(socksend_high_data)
                        time.sleep(1)
                        socksend_low_data = unhexlify('00060027'+convertdata[2:6]+low_crc+high_crc)
                        sock5.send(socksend_low_data)
                    else:
                        print "Display Data <= 65535"
                        socksend_high_data = unhexlify('00060026000069D0')
                        sock5.send(socksend_high_data)
                        time.sleep(1)
                        socksend_low_data = unhexlify('00060027'+convertdata+low_crc+high_crc)
                        sock5.send(socksend_low_data)
                except socket.error:
                    print"sock5 Display socket error"
                    TCP_connect(Nport4_ip_port)
        else:
            print("Waiting for incoming queue")
        tablename = 'correctiontime'
        get_sensor_data_from_DB(tablename)
        return_state = ""
        if Correction_Time_need_to_send != None:
            print"Correction time send"
            #convert Correction_Time_need_to_send to hex time
            #sensor_data = Correction_Time_need_to_send
            CMD = int(Correction_Time_need_to_send[0:2],16)
            tmp_data = Correction_Time_need_to_send[2:]
            recv_MAC_Level = CMD>>5
            print "recv_MAC_Level:",recv_MAC_Level
            if Self_MAC_Level != recv_MAC_Level:
                CMD = (Self_MAC_Level<<5) | (CMD & ~(1<<5 | 1<<6 | 1<<7))
            cmd_hex_data = binascii.hexlify(struct.pack(Endian + 'B', CMD))
            sensor_data = str(cmd_hex_data)+tmp_data
            sensor_macAddr = Source_MAC_address
            sensor_data_len = len(sensor_data)
            sensor_frameCnt = g_Frame_Count
            if sensor_macAddr[0:2] in my_dict_appskey:
                sensor_nwkskey = my_dict_nwkskey[sensor_macAddr[0:2]]
                sensor_appskey = my_dict_appskey[sensor_macAddr[0:2]]
                print("sensor_data:" + sensor_data )
                data_sending = "AT+SSTX=" + str(sensor_data_len) + "," + sensor_data + "," + sensor_macAddr[0:8] + "," + sensor_frameCnt + "," + sensor_nwkskey + "," + sensor_appskey + "\n"
                data_sending = str(data_sending)
                print data_sending
                #update DB sended flag here when sended and return status = "tx done        " bu nick
                ser.flushInput()
                ser.flushOutput()
                ser.write(data_sending)
                time.sleep(MY_SLEEP_INTERVAL)
                return_state = ser.readlines()
                #print(return_state)
            else:
                print('Not in ABP Group Config Rule, so give up')
                update_sensor_data_to_DB(2, sensor_macAddr, Correction_Time_need_to_send, sensor_frameCnt);

            if SENT_OK_TAG in return_state:
                print("Result: SENT.")
                #sended than update DB change sended flag to 1 by nick
                update_sensor_data_to_DB(2, sensor_macAddr, Correction_Time_need_to_send, sensor_frameCnt);
                Correction_Time_need_to_send = None
            else:
                print("Result: Send FAIL!")

            if 'ffffff' not in sensor_macAddr and 'FFFFFF' not in sensor_macAddr:
                #Send correctiontime ACK to application server or Microwave PC or Radio
                try:
                    print("Send correctiontime ACK to Application Server")
                    sock2.send(sensor_macAddr+sensor_data)
                except socket.error:
                    print"sock2 Application Server socket error"
                    TCP_connect(Application_Server_ip_port)
                try:
                    print("Send correctiontime ACK to Microwave PC")
                    sock3.send(sensor_macAddr+sensor_data)
                except socket.error:
                    print"sock3 Microwave PC socket error"
                    TCP_connect(Microwave_PC_ip_port)
                try:
                    print("Send correctiontime ACK to Radio")
                    sock4.send(sensor_macAddr+sensor_data)
                except socket.error:
                    print"sock4 Radio socket error"
                    TCP_connect(Nport3_ip_port)
        #time.sleep(MY_SLEEP_INTERVAL)

        tablename = 'retransmission'
        get_sensor_data_from_DB(tablename)
        return_state = ""
        if Retransmission_need_to_send != None:
            print"Retransmit send"
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
            if sensor_macAddr[0:2] in my_dict_appskey:
                sensor_nwkskey = my_dict_nwkskey[sensor_macAddr[0:2]]
                sensor_appskey = my_dict_appskey[sensor_macAddr[0:2]]
                print("sensor_data:" + sensor_data )
                data_sending = "AT+SSTX=" + str(sensor_data_len) + "," + sensor_data + "," + sensor_macAddr[0:8] + "," + sensor_frameCnt + "," + sensor_nwkskey + "," + sensor_appskey + "\n"
                data_sending = str(data_sending)
                print data_sending
                ser.flushInput()
                ser.flushOutput()
                ser.write(data_sending)
                time.sleep(MY_SLEEP_INTERVAL)
                return_state = ser.readlines()
                #print(return_state)
            else:
                print('Not in ABP Group Config Rule, so give up')
                update_sensor_data_to_DB(3, sensor_macAddr, Retransmission_need_to_send, sensor_frameCnt);

            if SENT_OK_TAG in return_state:
                print("Result: SENT.")
                #sended than update DB change sended flag to 1 by nick
                update_sensor_data_to_DB(3, sensor_macAddr, Retransmission_need_to_send, sensor_frameCnt);
                Retransmission_need_to_send = None
            else:
                print("Result: Send FAIL!")

        #To send LoRa repeater I/O status to  Diagnosis PC
        if g_sock1_flag == 0:
            report_status_to_diagnosis_pc()

if __name__ == "__main__":
    main()
