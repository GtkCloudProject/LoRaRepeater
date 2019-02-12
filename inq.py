#!/usr/bin/python

import paho.mqtt.client as mqtt
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
PC_ip_port = ('192.168.127.102',4007)

MAC_Address=0
MAC_Level=0
Sensor_Count=0
Endian = '>' #big-endian

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
        global MAC_Address, MAC_Level
        MAC_Address = check_my_dongle[check_my_dongle.find(REPLY_STRING) + 10: check_my_dongle.find(REPLY_STRING) + 18]
        print "MAC_Address:",MAC_Address
        if(MAC_Address[4:5]=='1'):
            MAC_Level = 1
        elif (MAC_Address[4:5]=='2'):
            MAC_Level = 2
        elif (MAC_Address[4:5]=='3'):
            MAC_Level = 3
        elif (MAC_Address[4:5]=='4'):
            MAC_Level = 4
        else:
            MAC_Level = 0
            print "MAC Level Error reset to 0"
        #my_logger.info('My USB dongle checked')
        return ser
        #else:
            #return None
    except serial.serialutil.SerialException:
        # print 'FAIL: Cannot open Serial Port (No LoRa Node Inserted)'
        return None

#connect_DB_put_data(3, sensor_mac, sensor_data, sensor_count)
def connect_DB_put_data(type, p_sensor_mac, p_sensor_data, p_sensor_count): #type 1:Water 2:Rain 3:Lora
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
            sql = "create table if not exists sensordata(source_mac_address CHAR(8) NOT NULL,time TIMESTAMP,raw_data CHAR(22),sended_flag BOOLEAN NOT NULL default 0, retransmit_flag BOOLEAN NOT NULL default 0, frame_count CHAR(8) NOT NULL, UNIQUE(source_mac_address, raw_data, frame_count))"
            cursor.execute(sql)
            SourceMACAddress = MAC_Address
            if type == 1:
                print("parameter = Water")
                sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', now(), '%s', %s)" % (SourceMACAddress, p_sensor_data, p_sensor_count)
                cursor.execute(sql)
                connection.commit()
            elif type == 2:
                print("parameter = Rain")
                sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', now(), '%s', %s)" % (SourceMACAddress, p_sensor_data, p_sensor_count)
                cursor.execute(sql)
                connection.commit()
            elif type == 3:
                print("parameter = Lora")
                tmp_time = time.localtime(int(p_sensor_data[2:10],16))
                sql = "insert ignore into sensordata (source_mac_address, time, raw_data, frame_count) values('%s', '%s', '%s', '%s')" % (p_sensor_mac[8:16],time.strftime('%Y-%m-%d %H:%M:%S',tmp_time) ,p_sensor_data, p_sensor_count)
                cursor.execute(sql)
                connection.commit()
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
    try:
        # print(msg.topic+" "+str(msg.payload))
        #print('Message incoming')
        #print(msg.topic)
        #print(msg.payload)
        json_data = msg.payload
        sensor_mac = json.loads(json_data)[0]['macAddr']
        sensor_data = json.loads(json_data)[0]['data']
        sensor_count = json.loads(json_data)[0]['frameCnt']
        nFrameCnt = json.loads(json_data)[0]['frameCnt']

        print('Data is:')
        print(sensor_data)

        print('now frameCnt is:')
        print(sensor_count)
# Store data to DB
# Check the frame doe not insert if data exist
        #if(lastframeCnt != sensor_count):
        print("Ready to put Lora data to DB")    
        connect_DB_put_data(3, sensor_mac, sensor_data, sensor_count)
            #lastframeCnt= sensor_count
        #else:
           # print("redundancy lora packet")
    except:
        my_logger.error('Received a non-UTF8 msg')

def TCP_connect(name):
    global sock1
    global sock2

    if name == Nport1_ip_port:
        try:
            sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock1.settimeout(1)
            sock1.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20)
            sock1.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)

            sock1.connect(Nport1_ip_port)
            print ("sock1 Water Meter connect")
        except:
            print("sock1 Water Meter error")
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
        except:
            print("sock2 Rain Meter error")
            pass

def main():
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
    print('I am started!')
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
    dot_str = ','
    TCP_connect(Nport1_ip_port)
    TCP_connect(Nport2_ip_port)
    global Sensor_Count
    while True:
        try:
            #Await a read event
            rlist, wlist, elist = select.select( [sock1, sock2], [], [], 5)
        except select.error:
            print "select error"

        for sock in rlist:
            if sock1 == sock: #water
                try:
                    recvdata, addr = sock.recvfrom(1024)
                    if recvdata:
                        print "received Water:"+str(recvdata)
                        Water = recvdata[recvdata.find(dot_str) +1:]
                        try:
                            Water_float = round(float(Water),2)
                        except:
                            Water_float =0
                        try:
                            Water_int = int(float(Water))
                        except:
                            Water_int =0
                        Water_decimal = int((Water_float - Water_int)*100)
                        Command = 1<<2
                        Data_Type = 1<<0
                        Command_MAC_Level = MAC_Level<<5
                        Time = int(time.time())
                        Timestamp = binascii.hexlify(struct.pack(Endian + 'I', Time))
                        CMD= Command_MAC_Level | Command | Data_Type
                        Water_format = binascii.hexlify(struct.pack(Endian + 'BLHB', CMD, Time, Water_int, Water_decimal))
                        print Water_format
                        Sensor_Count +=1
                        print"Sensor count:"+str(Sensor_Count)
                        connect_DB_put_data(1,MAC_Address,Water_format,Sensor_Count)
                    if not recvdata:
                        print "sock1 Water Meter disconnect"
                        TCP_connect(Nport1_ip_port)
                except socket.error:
                    print "sock1 Water Meter socket error"
                    time.sleep(5)
            elif sock2 == sock: #rain
                try:
                    recvdata, addr = sock.recvfrom(1024)
                    if recvdata:
                        print "received Rain:"+str(recvdata)
                        Rain = recvdata[recvdata.find(dot_str) + 1:]
                        try:
                           Rain_int = int(Rain)
                        except ValueError:
                           Rain_int = 0
                        Command = 1<<2
                        Data_Type = 2<<0
                        Command_MAC_Level = MAC_Level<<5
                        Time = int(time.time())
                        Timestamp = binascii.hexlify(struct.pack(Endian + 'I', Time))
                        CMD= Command_MAC_Level | Command | Data_Type
                        Rain_format = binascii.hexlify(struct.pack(Endian + 'BLH', CMD, Time, Rain_int))
                        print Rain_format
                        Sensor_Count+=1
                        print "Sensor count:"+str(Sensor_Count)
                        connect_DB_put_data(2,MAC_Address,Rain_format,Sensor_Count)
                    if not recvdata:
                        print "sock2 Rain Meter disconnect"
                        TCP_connect(Nport2_ip_port)
                except socket.error:
                    print "sock2 Rain Meter socket error"
                    time.sleep(5)
            else:
                print"Socket Else"

if __name__ == "__main__":
    main()
