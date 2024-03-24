#modified driver control code to mimic canbus data being sent from the motor controller to the driver screen
#TESTING PURPOSES ONLY
#gets random data and sends it using canbus to be displayed by the motor screen
#last worked on: 3/24/2024
#Mason Myre and Austin Kornerup



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

#Maximum RPM value
maxRPM = 0

#digital forward init
forward = digitalio.DigitalInOut(board.GP21)
forward.pull = digitalio.Pull.UP

#digital regen init
regen = digitalio.DigitalInOut(board.GP7)
regen.pull= digitalio.Pull.UP

#Analog value from the pedal
pedalPotentiometer = AnalogIn(board.A2)
potPercent = 0

#The node id we are sending to the Motor Controller
NODE_ID = 0x501

#Initialize the CAN object, baudrate 500k, cpu clock
mcp = CAN(spi, cs, baudrate = 500000, crystal_freq = 16000000, silent = False)


while True:

    #Constructor for the Message object(packing two floats(%,maxrpm))
    cputemp = microcontroller.cpu.temperature
    #send fake voltage and current data
    
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
    
    
    #send delay
    time.sleep(1)
