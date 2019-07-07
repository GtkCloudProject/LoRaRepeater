get_mac_addr.py : to get the mac addres of GL6509
set_mac_addr.py : to set the mac address of GL6509
    => to change xxxxxxxx to the mac address that you want in ser.write("AT+CDEVADDR=xxxxxxxx\r\n")
tcp_server_sample.py : the tcp server source code for testing => To send the correct time command and the resend command & to receive the response
    => To change tcp server ip in following line :
        bind_ip = "10.56.149.102"
        => Ex: if you want to set tcp server 10.56.147.176, please changing by following
            => bind_ip = "10.56.147.176"
        => For QA Testing, the IP of Application Server and Microwave_PC is both 10.56.147.176
        => For customer using, the IP of Application Server and Microwave PC is followed by the IP table of customer released
    => To change tcp server port in the following line :
        bind_port = 4006
        => Ex: if you want to set tcp server 4007, please changing by following
            => bind_port = 4007
        => For the port of Application Server is 4006
        => For the port of Microwave PC is 4007
    => To change the resend node the data of time that you want to
        resend_cmd = "050040d2095c7ba38d05"
        => To modify this line
    => To run : ./tcp_server_sample.py $action
        => ./tcp_server_sample.py 1 #to receive forward data
        => ./tcp_server_sample.py 2 #to send the correct time command and receive the response and the forward data
        => ./tcp_server_sample.py 3 #to send the resend command and receive the response and the forward data
    => To kill : killall tcp_server_sample.py


InsertDB.sh : To insert data to database
    =>run ./InsertDB.sh TableName{correctiontime | retransmission | sensordata} Count{number}
      e.g. ./InsertDB.sh sensordata 9999 =>means to insert 9999 data into sensordata table
      note: to Insert 100000 data into table may take about 1 hour time.
DeleteDB.sh : To delete data to database
    =>run ./DeleteDB.sh TableName{correctiontime | retransmission | sensordata} Count{number}
      e.g. ./DeleteDB.sh sensordata 9999 =>means to delete 9999 data from sensordata table
