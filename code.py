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

# NOTE: This code is goofy and does things with globals
# Initalize the SPI bus on the RP2040
# NOTE: Theses pins constant for all CAN-Pico Boards... DO NOT TOUCH
cs = digitalio.DigitalInOut(board.GP9)
cs.switch_to_output()
spi = busio.SPI(board.GP2, board.GP3, board.GP4)

#digital reverse init
reverse = digitalio.DigitalInOut(board.A1)
reverse.pull = digitalio.Pull.UP

#Maximum RPM value
omega = 0

#digital forward init
forward = digitalio.DigitalInOut(board.GP22)
forward.pull = digitalio.Pull.UP

#digital regen init
regen = digitalio.DigitalInOut(board.GP21)
regen.pull = digitalio.Pull.UP


#pedal = digitalio.DigitalInOut(board.GP25)
#pedal.direction = digitalio.Direction.OUTPUT
#Analog value from the pedal
pedalAnalog = AnalogIn(board.A0)
#The node id we are sending to the Motor Controller
NODE_ID = 0x501
#Initialize the CAN object, baudrate 500k, cpu clock
mcp = CAN(spi, cs, baudrate = 500000, crystal_freq = 16000000, silent = False)

t = Timer(timeout=5)
next_message = None
message_num = 0
tire_diameter = 22
last_send = time.monotonic_ns()#when our message was last sent
pedal_potentiometer_sum = 0
sample_count = 0
#pedal.value = True
start_time = time.monotonic()#since initalization

#Coil switch
CoilSwitch = digitalio.DigitalInOut(board.GP7)
CoilSwitch.pull = digitalio.Pull.UP

#Low Gear GP20 #High Gear A3

HighGear = digitalio.DigitalInOut(board.GP20)
HighGear.direction = digitalio.Direction.OUTPUT

LowGear = digitalio.DigitalInOut(board.A3)
LowGear.direction = digitalio.Direction.OUTPUT

LowGear.value = True
HighGear.value = False

IsCoilSwitched = False
LastCoilSwitchValue = True

Light = digitalio.DigitalInOut(board.GP18)
Light.direction = digitalio.Direction.OUTPUT

Light.value = False

def swap_coils():
    global IsCoilSwitched
    
    if IsCoilSwitched:
        Light.value = True
        HighGear.value = False
        sleep(0.5)
        LowGear.value = True
        Light.value = False
    else:
        Light.value = True
        LowGear.value = False
        sleep(0.5)
        HighGear.value = True
        Light.value = False

    IsCoilSwitched = not IsCoilSwitched

        
            
def send_message_over_can(maxrpm, thrust_percentage, IsCoilSwitched):
    '''This function is for sending the message of our calculatd maxrpm and percentage thrust over CAN, also updates our last_send and start_time variables to control how often we send messages'''
    global last_send
    global start_time

    #we do this because I don't want to modify the original code too much lol
    omega = maxrpm
    alpha = thrust_percentage

    #Constructor for the Message object(packing two floats(%,maxrpm))
    message = Message(id=0x501, data=struct.pack('<ff',omega,alpha), extended=False)
            
    #wait a little bit until you send another message
    while time.monotonic_ns() - last_send < 100000000:
        pass
                

    #send the message
    send_success1 = mcp.send(message)
    
    
    # Sending another message for coil switch
    #Constructor for the Message object()
    coil_message = Message(id=0x567, data=struct.pack('<B',IsCoilSwitched), extended=False)
            
    #wait a little bit until you send another message
    while time.monotonic_ns() - last_send < 100000000:
        pass
                

    #send the message
    send_success2 = mcp.send(coil_message)

    print("messages sent after {}s".format((time.monotonic_ns()-last_send)*10**-9))
    print(send_success1 and send_success2)
            
    last_send = time.monotonic_ns()
    start_time = time.monotonic()

def get_pedal_data():
    '''Gets pedal's potentiometer data and adds it to sum, this data is then reset at the end of the main loop to 0. Basically, we're summing it until it actually send the data at which point we reset to zero and start counting up again'''
    #pot means potentiometer I think
    # calc stands for calculator guys
    #grab pot value which is just pedal now that I acutally think about it
    pedalPercent = (pedalAnalog.value/63500)
    if pedalPercent < .05 :#dead band
        pedalPercent = 0
        
    return pedalPercent

def forward_neutral_reverse_regen(pedal_potentiometer_sum, sample_count):
    '''detects forward, neutral, reverse, regen selction and returns a list that contains the correct omega[maxrpm] and alpha[percentage thrust] as 0 and 1 indicies in the list'''
    #model function to describe acceleration
    thrust = (pow(pedal_potentiometer_sum/sample_count,1.75))*.9
    thrust = round(thrust,3)
    if thrust <=.01:#dead band on pedal
        thrust = 0
        
    #regen selected
    if not regen.value:
        Light.value = True
        return [0, thrust*0.80]
    else:
        Light.value = False
        
    #forward selected
    if not forward.value:
        return [20000, thrust]
    
    #reverse selected   
    if not reverse.value:
        return [-20000, thrust]

    #neutral select
    if  forward.value and reverse.value:
        return [0,0]

    #THIS SHOULD NEVER BE REACHED, JUST PUTTING HERE JUST IN CASE
    return [0,0]

def coilSwitchButton():
    #This is logic to detect a single gbutton press, and not continually switch coils while button is held, instead oly doing it w=once per nbutton press.
    global LastCoilSwitchValue
    
    CoilButtonPressed = not CoilSwitch.value

    if CoilButtonPressed and not LastCoilSwitchValue:
        swap_coils()
    
    LastCoilSwitchValue = CoilButtonPressed

def main():
    '''main data gathering and then message sending loop.'''
    while True:
        global pedal_potentiometer_sum
        global sample_count
        global IsCoilSwitched
        global LastCoilSwitchValue
        
        #were summing data here until we actually send a message
        pedal_potentiometer_sum += get_pedal_data()
        sample_count +=1
        
        #This is if is basiclly just checking if 0.1 seconds have passed, since we reset start_time in the send_message function
        if time.monotonic()-start_time >= 0.1:

            maxrpm_thrust_list = forward_neutral_reverse_regen(pedal_potentiometer_sum, sample_count) # get our maxrpm and thrust depending on switch
    
            
            #Picks up if coil switch button has been activated and swaps our boolean if so
            coilSwitchButton()
            
            maxrpm = maxrpm_thrust_list[0]
            thrust_percentage = maxrpm_thrust_list[1]
            
            send_message_over_can(maxrpm, thrust_percentage, IsCoilSwitched) # send our maxrpm and thrust over CAN

            #reseting our data to zero before we begin sampling again

            pedal_potentiometer_sum = 0
            sample_count = 0

main()
       
       
     


