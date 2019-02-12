#!/usr/bin/python

import os
import json
import sys
import time
import serial
import logging
import pymysql.cursors
import socket

from logging.handlers import RotatingFileHandler

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

Data_need_to_send = None
g_Frame_Count = ""
Source_MAC_address = ""

Nport1_ip_port = ('192.168.127.88',4001) #water meter
Nport2_ip_port = ('192.168.127.88',4002) #rain meter
Nport3_ip_port = ('192.168.127.88',4003) #radio
Nport4_ip_port = ('192.168.127.88',4004) #display
Diagnosis_PC_ip_port = ('192.168.127.178',4005)
Application_Server_ip_port = ('192.168.127.178',4006)
Microwave_PC_ip_port = ('192.168.127.102',4007)

Nport1_connect_status = False #water meter
Nport2_connect_status = False #rain meter
Nport3_connect_status = False #radio
Nport4_connect_status = False #display
Diagnosis_PC_connect_status = False
Application_Server_connect_status = False
Microwave_PC_connect_status = False

my_dict_appskey = {}
my_dict_nwkskey = {}

#add by nick
def TCP_connect(name):
    global sock1
    global sock2
    global sock3
    global sock4
    global sock5
    global Diagnosis_PC_connect_status
    global Application_Server_connect_status
    global Microwave_PC_connect_status
    global Nport1_connect_status
    global Nport2_connect_status
    global Nport3_connect_status
    global Nport4_connect_status
    if name == Diagnosis_PC_ip_port:
        try:
            sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock1.settimeout(1)
            sock1.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock1.connect(Diagnosis_PC_ip_port)
            Diagnosis_PC_connect_status = True
            print "sock1 Diagnosis PC connect"
        except:
            print "sock1 error"
            pass
    elif name == Application_Server_ip_port:
        try:
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock2.settimeout(1)
            sock2.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock2.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock2.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock2.connect(Application_Server_ip_port)
            Application_Server_connect_status = True
            print "sock2 Application Server connect"
        except:
            print"sock2 error"
            pass
    elif name == Microwave_PC_ip_port:
        try:
            sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock3.settimeout(1)
            sock3.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock3.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock3.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock3.connect(Microwave_PC_ip_port)
            Microwave_PC_connect_status = True
            print "sock3 Microwave PC connect"
        except:
            pass
    elif name == Nport3_ip_port:
        try:
            sock4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock4.settimeout(1)
            sock4.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock4.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock4.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock4.connect(Nport3_ip_port)
            Nport3_connect_status = True
            print "sock4 Radio connect"
        except:
            pass
    elif name == Nport4_ip_port:
        try:
            sock5 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock5.settimeout(1)
            sock5.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock5.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock5.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            sock5.connect(Nport4_ip_port)
            Nport4_connect_status = True
            print "sock5 Display connect"
        except:
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
def get_sensor_data_from_DB():
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
            try:
                sql = "select sended_flag, raw_data, source_mac_address, frame_count from sensordata WHERE sended_flag='0' limit 1"
                cursor.execute(sql)
                global Source_MAC_address
                global g_Frame_Count           
                global Data_need_to_send
                #print cursor.rowcount
                if(cursor.rowcount>0):
                    for row in cursor:
                        Data_need_to_send = row["raw_data"]
                        Source_MAC_address = row["source_mac_address"]
                        g_Frame_Count = row["frame_count"]
                        print "Source_MAC_address: " ,Source_MAC_address
                        print "Data_need_to_send: ",Data_need_to_send
                        print "Frame Count:", g_Frame_Count
                else:   
                    print "DB return null"
                    Data_need_to_send = None
            except:
                connection.rollback()
    finally:
        connection.close()

#add by nick
def update_sensor_data_to_DB(l_sensor_macAddr, l_sensor_data, l_sensor_frameCnt):
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

            sql = "update sensordata set sended_flag=1 where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s'" % (l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt) 
            cursor.execute(sql)
            connection.commit()

            tmp_time = time.localtime(int(l_sensor_data[2:10],16))
            sql = "update sensordata set time='%s' where source_mac_address='%s' AND raw_data='%s' AND frame_count='%s' AND sended_flag=1" % (time.strftime('%Y-%m-%d %H:%M:%S',tmp_time), l_sensor_macAddr[0:8], l_sensor_data, l_sensor_frameCnt)
            cursor.execute(sql)
            connection.commit()

    finally:
        connection.close()

def check_lora_module(dev_path):
    try:
        ser = serial.Serial(dev_path, 9600, timeout=0.5)
        ser.flushInput()
        ser.flushOutput()
        ser.write("AT\r\n")
        #time.sleep(3)
        check_my_dongle = ser.readlines()
        #if any(REPLY_OK_STRING in s for s in check_my_dongle):
        #print('My USB dongle checked')
        return ser
        #else:
            #return None
    except serial.serialutil.SerialException:
        # print 'FAIL: Cannot open Serial Port (No LoRa Node Inserted)'
        return None

def main():
    global Data_need_to_send
    Data_need_to_send = None

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
        ser = check_lora_module(devPath)
        if ser is None:
            continue
        else:
            global_check_dongle_exist = True
            #print('Open LoRa node done:')

            #print(devPath)
            break

    if global_check_dongle_exist is False:
        my_logger.error('no device be detected, exit!!!')
        sys.exit()

    my_dict = {}
    time_dict= {}
    TCP_connect(Diagnosis_PC_ip_port)
    TCP_connect(Application_Server_ip_port)

    #TCP_connect(PC_ip_port)
    #TCP_connect(Nport3_ip_port)
    #TCP_connect(Nport4_ip_port)

    while 1:
        get_sensor_data_from_DB()
        if Data_need_to_send != None:
            print "a packet need to send"
            sensor_data = Data_need_to_send
            sensor_macAddr = Source_MAC_address
            sensor_data_len = len(sensor_data)
            #for test, need fix
            sensor_frameCnt =""  #store in DB or caculate by repeater? by nick
            sensor_nwkskey = ""
            sensor_appskey = ""
            sensor_frameCnt = g_Frame_Count
            if sensor_macAddr[0:2] in my_dict_appskey:
                sensor_nwkskey = my_dict_nwkskey[sensor_macAddr[0:2]]
                sensor_appskey = my_dict_appskey[sensor_macAddr[0:2]]
            else:
                my_logger.info('Not in ABP Group Config Rule, so give up')

            print("sensor_data:" + sensor_data )
            # data_sending = "AT+DTX="+str(sensor_data_len)+","+sensor_data+"\n"
            data_sending = "AT+SSTX=" + str(sensor_data_len) + "," + sensor_data + "," + sensor_macAddr[0:8] + "," + sensor_frameCnt + "," + sensor_nwkskey + "," + sensor_appskey + "\n"
            data_sending = str(data_sending)
            print data_sending
            #send data to Application Server that if connected
            try:
                if (Application_Server_connect_status == True):
                    sock2.send(sensor_macAddr+sensor_data)
            except socket.error:
                print"sock2 Application_Server socket error"
                TCP_connect(Application_Server_ip_port)
            #GLOBAL_TIME_RUNNING += MY_SLEEP_INTERVAL

            my_logger.info('Sending')
            ser.flushInput()
            ser.flushOutput()
            ser.write(data_sending)
            #sock.send(data_sending)
            #my_logger.info(data_sending)
            time.sleep(MY_SLEEP_INTERVAL)
            return_state = ser.readlines()
            print(return_state)
            my_logger.info(return_state)
            update_sensor_data_to_DB(sensor_macAddr, sensor_data, sensor_frameCnt);
            Data_need_to_send = None
            if SENT_OK_TAG in return_state:
                time.sleep(MY_SLEEP_INTERVAL)
                print("Result: SENT.")
                #sended than update DB change sended flag to 1 by nick
                update_sensor_data_to_DB(sensor_macAddr, sensor_data, sensor_frameCnt);             
                #my_logger.info('Result: SENT.')
                #GLOBAL_COUNT_SENT += 1
                #os.rename(MY_SENDING_FILE_PATH + sending_f, MY_SENT_FILE_PATH + sending_f)
            else:
                time.sleep(MY_SLEEP_INTERVAL)
                print("Result: FAIL! move to FAIL")
                #my_logger.error('Result: FAIL! move to FAIL.')
                #GLOBAL_COUNT_FAIL += 1
                #os.rename(MY_SENDING_FILE_PATH + sending_f, MY_SEND_FAIL_FILE_PATH + sending_f)
            #add Radio Send by nick
            try:
                TCP_connect(Nport3_ip_port) #radio interface
                sock4.send(sensor_macAddr+sensor_data)
            except socket.error:
                print"sock4 Radio socket error"
                TCP_connect(Nport3_ip_port)
        else:
             print("Waiting for incoming queue")
        #add Diagnosis_PC Send by nick
        try:
            if (Diagnosis_PC_connect_status == True):
                sock1.send("Repeater Status OK")
        except socket.error:
            print"sock1 Diagnosis_PC socket error"
            TCP_connect(Diagnosis_PC_ip_port)
        time.sleep(5)
if __name__ == "__main__":
    main()
