#!/usr/bin/python
import os
import sys
import time
import serial

MAC_RES = "+CDEVADDR:"
def main():
    try:
        ser = serial.Serial("/dev/ttyS0", 9600, timeout=0.5)
        ser.flushInput()
        ser.flushOutput()

        print('=== Get Channel Setting===')

        ser.write("AT+CQCH?\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)


        return ser
    except serial.serialutil.SerialException:
            # print 'FAIL: Cannot open Serial Port (No LoRa Node Inserted)'
            return None

if __name__ == "__main__":
    main()
