get_mac_addr.py : to get the mac addres of GL6509
set_mac_addr.py : to set the mac address of GL6509
    => to change xxxxxxxx to the mac address that you want in ser.write("AT+CDEVADDR=xxxxxxxx\r\n")
tcp_server_sample.py : the tcp server source code for testing => To send the correct time command and the resend command & to receive the response
    => To change tcp server ip :
        bind_ip = "192.168.127.101"
        => Ex: if you want to set tcp server 192.168.127.102, please changing by following
            => bind_ip = "192.168.127.102"
    => To change tcp server port :
        bind_port = 4006
        => Ex: if you want to set tcp server 4007, please changing by following
            => bind_port = 4007
    => To change the resend node the data of time that you want to
        resend_cmd = "050040d2095c7ba38d05"
        => To modify this line
    => To run : ./tcp_server_sample.py
    => To kill : killall tcp_server_sample.py
