#!/usr/bin/python
import serial
import time
def main():
    try:
        ser = serial.Serial("/dev/ttyS0", 9600, timeout=0.5)
        ser.flushInput()
        ser.flushOutput()

        ser.write("AT+CTXPS=1,0,7\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        ser.write("AT+CSLRM\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        ser.write("AT&W\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        ser.write("ATZ\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        return ser
    except serial.serialutil.SerialException:
            # print 'FAIL: Cannot open Serial Port (No LoRa Node Inserted)'
            return None

if __name__ == "__main__":
    main()
