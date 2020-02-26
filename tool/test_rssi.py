#!/usr/bin/python
import os
import sys
import time
import serial

MAC_RES = "+CDEVADDR:"
def main():
    try:
        print("=== To start to test LoRa signal by sending 20 lora packets ===")

        total_count = int(sys.argv[1]) + 2
        os.system('killall check_repeater.sh inq.py deq.py')

        ser = serial.Serial("/dev/ttyS0", 9600, timeout=0.5)
        ser.flushInput()
        ser.flushOutput()

        ser.write("AT+CQCH?\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        if len(sys.argv) >= 3:
            if int(sys.argv[2]) == 10:
                print('sys.argv[2] == 10')
                ser.write("AT+CADR=2,0,FFFF,0,1\r\n")
                return_state = ser.readlines()
                print(return_state)
                time.sleep(2)
            elif int(sys.argv[2]) == 12:
                print('sys.argv[2] == 12')
                ser.write("AT+CADR=0,0,FFFF,0,1\r\n")
                return_state = ser.readlines()
                print(return_state)
                time.sleep(2)
            else:
                print('sys.argv is Invalid value - SF 10')
                ser.write("AT+CADR=2,0,FFFF,0,1\r\n")
                return_state = ser.readlines()
                print(return_state)
                time.sleep(2)

        ser.write("AT+CADR?\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        ser.write("AT+CTXPS=1,0,7\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        ser.write("AT+CTXPS?\r\n")
        return_state = ser.readlines()
        print(return_state)
        time.sleep(2)

        ser.write("AT+CDEVADDR?\r\n")
        check_my_dongle = ""
        check_my_dongle = str(ser.readlines())
        MAC_Address = check_my_dongle[check_my_dongle.find(MAC_RES) + 10: check_my_dongle.find(MAC_RES) + 18]

        for count1 in range(total_count):
            if len(sys.argv) >= 3:
                if int(sys.argv[2]) == 10:
                    print('sys.argv[2] == 10')
                    ser.write("AT+CADR=2,0,FFFF,0,1\r\n")
                    return_state = ser.readlines()
                    print(return_state)
                    time.sleep(1)
                elif int(sys.argv[2]) == 12:
                    print('sys.argv[2] == 12')
                    ser.write("AT+CADR=0,0,FFFF,0,1\r\n")
                    return_state = ser.readlines()
                    print(return_state)
                    time.sleep(1)
                else:
                    print('sys.argv is Invalid value - SF 10')
                    ser.write("AT+CADR=2,0,FFFF,0,1\r\n")
                    return_state = ser.readlines()
                    print(return_state)
                    time.sleep(1)
            ser.write("AT+CTXPS=1,0,7\r\n")
            return_state = ser.readlines()
            print(return_state)
            time.sleep(1)
            if count1 == 1:
                ser.write("AT+SSTX=22,3531313435363738393061,"+MAC_Address+",1,BA21C6216312C334597D88711D9EFABE,BA21C6216312C334597D88711D9EFABE\r\n")
                return_state = ser.readlines()
                print(return_state)
                time.sleep(10)
            elif count1==0:
                continue
            else:
                ser.write("AT+SSTX=22,3132333435363738393061,"+MAC_Address+","+str(count1)+",BA21C6216312C334597D88711D9EFABE,BA21C6216312C334597D88711D9EFABE\r\n")
                #ser.write(snd_str)
                return_state = ser.readlines()
                print(return_state)
                time.sleep(10)

        print("=== To finish to test the LoRa signal by sending 20 lora packets ===")
        return ser
    except serial.serialutil.SerialException:
            # print 'FAIL: Cannot open Serial Port (No LoRa Node Inserted)'
            return None

if __name__ == "__main__":
    main()
