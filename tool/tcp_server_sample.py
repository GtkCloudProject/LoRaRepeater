#!/usr/bin/python

"""
TCP/IP Server sample
"""
import socket
import threading
import time

bind_ip = "192.168.127.101"
#bind_ip = "0.0.0.0"
bind_port = 4006

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

server.bind((bind_ip, bind_port))

server.listen(5)

#print "[*] Listening on %s:%d" % (bind_ip, bind_port)
print "[%s] To listen on %s:%d" % (time.asctime(time.localtime(time.time())), bind_ip, bind_port)

def handle_client(client_socket):
    #print "[*] To start a new client socket"
    print "[%s] To start a new client socket" % (time.asctime(time.localtime(time.time())))
    correct_time_flag = 1
    resend_flag = 1
    while True:
        time.sleep(1)
        try:
            if correct_time_flag == 1 :
                correct_time_flag = 0
                now_time = int(time.time())
                now_time_str = "%x" % now_time
                correct_time_cmd = "05ffffff04%s" %(now_time_str)
                client_socket.send(correct_time_cmd)
                #print "[*] To send the correct time command : %s" % (correct_time_cmd)
                print "[%s] To send the correct time command : %s" % (time.asctime(time.localtime(time.time())), correct_time_cmd)

            if resend_flag == 1 :
                resend_flag = 0
                resend_cmd = "050040d2095c7ba38d05"
                client_socket.send(resend_cmd)
                #print "[*] To send the resend command       : %s" % (correct_time_cmd)
                print "[%s] To send the resend command       : %s" % (time.asctime(time.localtime(time.time())), resend_cmd)

            response = client_socket.recv(1024)
            if response[8:10] == "84" :
                #print "[*] The correct time response : %s" % (response)
                print "[%s] The correct time response : %s" % (time.asctime(time.localtime(time.time())), response)
            elif response[8:10] == "81" :
                #print "[*] The forward data response : %s" % (response)
                print "[%s] The forward data response : %s" % (time.asctime(time.localtime(time.time())), response)
            elif response[8:10] == "89" or response[8:10] == "8a" :
                #print "[*] The re-send data response : %s" % (response)
                print "[%s] The re-send data response : %s" % (time.asctime(time.localtime(time.time())), response)
            else:
                #print "[*] The unknown data response : %s" % (response)
                print "[%s] The unknown data response : %s" % (time.asctime(time.localtime(time.time())), response)

            #client_socket.close()

        except socket.error:
            #print "[*] send error"
            print "[%s] send error" % (time.asctime(time.localtime(time.time())))

while True:
    client, addr = server.accept()
    #print "[*] Acepted connection from: %s:%d" % (addr[0],addr[1])
    print "[%s] To be acepted connection from %s:%d" % (time.asctime(time.localtime(time.time())), addr[0], addr[1])
    client_handler = threading.Thread(target=handle_client, args=(client,))
    client_handler.start()
