import serial
import time

ser = serial.Serial()
ser.port = "/dev/ttyS4"
ser.baudrate = 9600
ser.bytesize = serial.EIGHTBITS  # number of bits per bytes
ser.parity = serial.PARITY_NONE  # set parity check: no parity
ser.stopbits = serial.STOPBITS_ONE
ser.timeout = 1  # timeout block read
ser.xonxoff = False  # disable software flow control
ser.rtscts = False  # disable hardware (RTS/CTS) flow control
ser.dsrdtr = False  # disable hardware (DSR/DTR) flow control
ser.writeTimeout = 2  # timeout for write


def open_sr():
    try:
        ser.open()
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.2)
        print("Serial Opened")
    except Exception as e:
        print("error open serial port: " + str(e))


def close_sr():
    try:
        ser.close()

        print("Serial Closed")
    except Exception as e:
        print("error close serial port: " + str(e))


def snd_sr(data):
    if ser.isOpen():

        try:
            ser.write(str.encode(data))
            print("Data Sent : ", data)
            time.sleep(0.2)
        except Exception as e:
            print("From snd sr : ", e)


def rcv_sr():
    if ser.isOpen():
        try:
            response = ser.readline()
            return response
        except Exception as e:
            print("Error at rcv sr : ", e)


if __name__ == '__main__':
    open_sr()

    # while 1:
    #     res = rcv_sr()
    #     print("Response : ", res)
    # snd_sr("?01Z?08Z?15Z?16Z?17Z?18Z")
    snd_sr("?16Z")
