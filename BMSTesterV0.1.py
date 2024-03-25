#testing code to mimic BMS data being sent to the BMS driver display screen
#TESTING PURPOSES ONLY
#gets random data and sends it using canbus to be displayed by the motor screen
#last worked on: 3/24/2024
#Mason Myre



import board
import busio
from analogio import AnalogIn
from time import sleep
import struct
import digitalio
from adafruit_mcp2515       import MCP2515 as CAN
from adafruit_mcp2515.canio import RemoteTransmissionRequest, Message, Match, Timer
import math
import time
import random
import microcontroller


# Initalize the SPI bus on the RP2040
# NOTE: Theses pins constant for all CAN-Pico Boards... DO NOT TOUCH
cs = digitalio.DigitalInOut(board.GP9)
cs.switch_to_output()
spi = busio.SPI(board.GP2, board.GP3, board.GP4)

#digital reverse init
reverse = digitalio.DigitalInOut(board.GP22)
reverse.pull= digitalio.Pull.UP


#Initialize the CAN object, baudrate 500k, cpu clock
mcp = CAN(spi, cs, baudrate = 500000, crystal_freq = 16000000, silent = False)

lowVolt = int(3.3273 * 1000)
highVolt = int(3.3705 * 1000)
highTemp = 28
amps = int(13.7 * 10)
voltage = int(114.3 * 10)

#other garbage data just to make sending more universal
packAmpHours = 100
summedVoltage = 100
lowTemp = 20
avgTemp = 23
avgVolt = int(3.3423 * 1000)
highCellNum = 12
lowCellNum = 8

while True:

    #Constructor for the Message object(packing two floats(%,maxrpm))
    #send fake voltage and current data
    

    #this is different than what is on the teams but the teams is wrong
    message = Message(id=0x6B0, data=struct.pack('<HHHH', packAmpHours, amps, summedVoltage, voltage))
    send_success = mcp.send(message)
    print(send_success)
    
    message = Message(id=0x6B1, data=struct.pack('HHHxx', lowTemp, highTemp, avgTemp))
    send_success = mcp.send(message)
    print(send_success)
    
    message = Message(id=0x6B2, data=struct.pack('HHHBB', highVolt, lowVolt, avgVolt, highCellNum, lowCellNum))
    print(send_success)
    print()
    
    '''
    rpm = round(random.uniform(0,650), 2)
    curr = round(random.uniform(0,69), 2)
    message = Message(id=0x402, data=struct.pack('<ff',rpm, curr), extended=False)
    send_success = mcp.send(message)

    motorTemp = round(random.uniform(10,85),2)
    heatsinkTemp = round(random.uniform(10,85),2)
    message = Message(id=0x40B, data=struct.pack('<ff',motorTemp, heatsinkTemp), extended=False)
    send_success = mcp.send(message)
 

   # message = Message(id=0x40B, data=struct.pack('<IIII',0,0,0,0), extended=False)
   # send_success = mcp.send(message)
    
    '''
    #send delay
    time.sleep(1)
