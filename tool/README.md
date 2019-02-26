get_mac_addr.py : to get the mac addres of GL6509
set_mac_addr.py : to set the mac address of GL6509
    => to change xxxxxxxx to the mac address that you want in ser.write("AT+CDEVADDR=xxxxxxxx\r\n")
tcp_server_sample.c : the tcp server source code for testing
    => To change tcp server port :
        #define ROBOT_LISTEN_PORT 4006
        => Ex: if you want to set tcp server 4007, please changing by following
            => #define ROBOT_LISTEN_PORT 4007
    => To compile : gcc -o tcp_server_sample tcp_server_sample.c
    => To run : ./tcp_server_sample
