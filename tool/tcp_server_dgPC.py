#!/usr/bin/python

"""
TCP/IP Server sample
"""
import socket
import threading
import time
import sys
import binascii
import struct

bind_ip = "10.56.149.240"
bind_port = 4008

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server.bind((bind_ip,bind_port))

server.listen(5)
#print "[*] Listening on %s:%d" % (bind_ip, bind_port)
print ("[%s] To listen on %s:%d" % (time.asctime(time.localtime(time.time())), bind_ip, bind_port))

def handle_client(client_socket):
    #print "[*] To start a new client socket"
    print ("[%s] To start a new client socket" % (time.asctime(time.localtime(time.time()))))

    if sys.argv[1] == "2" : #For the correct time command
        correct_time_flag = 1
        resend_flag = 0
    elif sys.argv[1] == "3" : #For the resend command
        correct_time_flag = 0
        resend_flag = 1
    else : #For forward command
        correct_time_flag = 0
        resend_flag = 0
    count = 0
    while True:
        time.sleep(1)
        try:
            if correct_time_flag == 1 :
                correct_time_flag = 0
                now_time = int(time.time())
                now_time = now_time + 28800
                now_time_str = "%x" % now_time
                correct_time_cmd = "05ffffff04%s" %(now_time_str)
                correct_time_cmd_hex = bytearray.fromhex(unicode(correct_time_cmd))
                client_socket.send(correct_time_cmd_hex)
                #print "[*] To send the correct time command : %s" % (correct_time_cmd)
                print ("[%s] To send the correct time command : %s" % (time.asctime(time.localtime(time.time())), correct_time_cmd))

            if resend_flag == 1:
                resend_flag = 0
                if(len(sys.argv)) == 3:
                    resend_cmd = str(sys.argv[2])
                else:
                    resend_cmd = "05002005095E281E1001"
                print('Bill_Log1_str(sys.argv[2]):'+str(sys.argv[2]))
                print('Bill_Log1_str:' + "05002005095E281E1001")
                resend_cmd_hex = bytearray.fromhex(unicode(resend_cmd))
                client_socket.send(resend_cmd_hex)
                #print "[*] To send the resend command       : %s" % (correct_time_cmd)
                print ("[%s] To send the resend command       : %s" % (time.asctime(time.localtime(time.time())), resend_cmd))
            print("\r")
            response_hex = client_socket.recv(1024)
            response = str(binascii.hexlify(response_hex))
            print ("response: %s" % response)
            macaddr = response[0:8]
            print ("macaddr: %s" % macaddr)
            recvtime = response[10:18]
            print ("recvtime: %s" % recvtime)
            tmp_time = time.gmtime(int(recvtime,16))
            print ("tmp_time: %s" % tmp_time)
            strtime = time.strftime('%Y-%m-%d %H:%M:%S',tmp_time)
            print ("strtime: %s" % strtime)
            if response[8:10] == "84" or response[8:10] == "24": #24 is for nick test
                #print "[*] The correct time response : %s" % (response)
                print ("[%s] The correct time response : %s" % (time.asctime(time.localtime(time.time())), response))
                print ("[%s] MacAddr: %s, Time: %s" % (time.asctime(time.localtime(time.time())), macaddr, strtime))
            elif response[8:10] == "81" or response[8:10] == "82" or response[8:10] == "21" or response[8:10] == "22": #21 and 22 is for nick test
                #print "[*] The forward data response : %s" % (response)
                print ("[%s] The forward data response : %s" % (time.asctime(time.localtime(time.time())), response))
                if response[9:10] =='1':
                    type = 'water'
                else:
                    type = 'rain'
                data = '%s.%s' % (str(int(response[18:22], 16)), str(int(response[22:24], 16)))
                if response[24:26] =='00':
                    power_status = 'Interruption'
                else:
                    power_status = 'Normal'
                print ("[%s] MacAddr: %s, Time: %s, DataType: %s, Data: %s, Power Status: %s" % (time.asctime(time.localtime(time.time())), macaddr, strtime, type, data, power_status))
            elif response[8:10] == "89" or response[8:10] == "8a" or response[8:10] == "29" or response[8:10] == "2a": #29 and 2a is for nick test
                #print "[*] The re-send data response : %s" % (response)
                print ("[%s] The re-send data response : %s" % (time.asctime(time.localtime(time.time())), response))
                if response[9:10] =='9':
                    type = 'water'
                else:
                    type = 'rain'
                data = '%s.%s' % (str(int(response[18:22], 16)), str(int(response[22:24], 16)))
                if response[24:26] =='00':
                    power_status = 'Interruption'
                else:
                    power_status = 'Normal'
                print ("[%s] MacAddr: %s, Time: %s, DataType: %s, Data: %s, Power Status: %s" % (time.asctime(time.localtime(time.time())), macaddr, strtime, type, data, power_status))

            else:
                #print "[*] The unknown data response : %s" % (response)
                print ("[%s] The unknown data response : %s" % (time.asctime(time.localtime(time.time())), response))

            #client_socket.close()

        except socket.error:
            #print "[*] send error"
            print ("[%s] send error" % (time.asctime(time.localtime(time.time()))))

while True:
    client, addr = server.accept()
    #print "[*] Acepted connection from: %s:%d" % (addr[0],addr[1])
    print ("[%s] To be acepted connection from %s:%d" % (time.asctime(time.localtime(time.time())), addr[0], addr[1]))
    client_handler = threading.Thread(target=handle_client, args=(client,))
    client_handler.start()
