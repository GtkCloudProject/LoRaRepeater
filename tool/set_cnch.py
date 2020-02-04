#!/usr/bin/python
import os
import sys
import time
import serial

MAC_RES = "+CDEVADDR:"
def main():
    try:
        print("=== Setting Cannal value ===")

        channel_value = int(sys.argv[1]) + 2

        ser = serial.Serial("/dev/ttyS0", 9600, timeout=0.5)
        ser.flushInput()
        ser.flushOutput()

        ser.write("AT+CQCH?\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        if len(sys.argv) < 2:
            print('sys.argv is Invalid value')
            return ser

        if int(sys.argv[1]) >= 16:
            for i in range(16):
                if i <= 11:
                    value = 9200000 + (i + 1) * 2000
                else:
                    value = 9200000 + 6000 + (i + 1) * 2000
                cmd = "AT+CNCH=" + str(hex(i))[2:] + "," + str(value) + ",5,0\r\n"
                print(cmd)
                ser.write(cmd)
                return_state = ser.readlines()
                print(return_state)
                time.sleep(2)
        else:
            for i in range(16):
                if int(sys.argv[1]) <= 11:
                    value = 9200000 + (int(sys.argv[1]) + 1) * 2000
                else:
                    value = 9200000 + 6000 + (int(sys.argv[1]) + 1) * 2000
                cmd = "AT+CNCH=" + str(hex(i))[2:] + "," + str(value) + ",5,0\r\n"
                print(cmd)
                ser.write(cmd)
                return_state = ser.readlines()
                print(return_state)
                time.sleep(2)
        return ser
    except serial.serialutil.SerialException:
            # print 'FAIL: Cannot open Serial Port (No LoRa Node Inserted)'
            return None

if __name__ == "__main__":
    main()
