'''
Last Edit: 05/26/2023


The Following code is for the driver display

Please make sure to include the following in the lib folder:
adafruit_display_text
adafruit_mcp2515
adafruit_ssd1325.py


'''

import board
import busio
import math
import struct
import time
import analogio
import digitalio
import displayio
import terminalio
import adafruit_ssd1325
from adafruit_mcp2515       import MCP2515 as CAN
from adafruit_mcp2515.canio import RemoteTransmissionRequest, Message, Match, Timer
from adafruit_display_text import label
import adafruit_mcp2515
import microcontroller
import fourwire
from adafruit_progressbar.verticalprogressbar import VerticalProgressBar, VerticalFillDirection

#--------------Bogus Ahh Initalization stuff--------------------------#

# Release the displays and start the claock
boot_time = time.monotonic()
displayio.release_displays()

# Create the SPI Buss
spi = busio.SPI(board.GP2, board.GP3, board.GP4)

uart = busio.UART(board.GP0,board.GP1,baudrate=9600)

# Set up the MCP 2515 on the SPI Bus
can_cs = digitalio.DigitalInOut(board.GP9)
can_cs.switch_to_output()
mcp = CAN(spi, can_cs, baudrate = 500000, crystal_freq = 16000000, silent = False,loopback = False)

# Set up the OLED on the SPI Bus
cs = board.GP20
dc = board.GP10
reset = board.GP19
WIDTH = 128
HEIGHT = 64
BORDER = 0
FONTSCALE = 1

display_bus = fourwire.FourWire(spi, command=dc, chip_select=cs, reset=reset, baudrate=1000000)
display = adafruit_ssd1325.SSD1325(display_bus, width=WIDTH, height=HEIGHT)
display.brightness = 1.0



startTime = time.time()
# Make the display context
splash = displayio.Group()
display.root_group = splash

# Startup
text = "SOLAR CAR ISU\nDriver Screen"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
text_width = text_area.bounding_box[2] * FONTSCALE
text_group = displayio.Group(
    scale=FONTSCALE,
    x=display.width // 2 - text_width // 2,
    y=display.height // 2,
)
text_group.append(text_area)  # Subgroup for text scaling
splash.append(text_group)
time.sleep(2.5)
splash.pop(-1)


tire_diameter = 22
mph     = 0
voltage = 0
current = 0
heatsink_temp = 0
motor_temp = 0
DCU_timeout = 0
prevDCU_time = time.monotonic_ns()
odometer = 0
sendtime=time.time()
drawtime=time.time()

time.sleep(0.2)


#defining some stuff for the progress bars to be used elsewhere.

testValue1 = 0

amp_bar = VerticalProgressBar(
    (30, 33),#position
    (20, 30),#size
    bar_color=0xFFFFFF,
    outline_color = 0x000000,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 0
)

'''
motor_temp_bar = VerticalProgressBar(
    (30, 24),#position
    (20, 38),#size
    bar_color=0xFFFFFF,
    outline_color = 0x000000,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 50
)

heat_sink_bar = VerticalProgressBar(
    (30, 24),#position
    (20, 38),#size
    bar_color=0xFFFFFF,
    outline_color = 0x000000,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 50
)
'''

#--------------Screen Drawing--------------------------#

def initScreen():
    global amp_bar
    
    
    splash.append(amp_bar)
    
    
    
    #keeping old screen code for now, below return
    return
    #Draw Odometer Label
    text_group = displayio.Group(scale=1, x=2, y=8)
    text = "TRIP: {:04.1f}".format(odometer)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)
    
        # Draw Speed/effecency Label
    text_group = displayio.Group(scale=1, x=2, y=27)
    text = "MPH: {:04.1f}".format(mph)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)

    # Draw Efficiency Label
    text_group = displayio.Group(scale=1, x=2, y=46)
    text = "Amp: {:04.1f}".format(current)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)

    # Draw voltage/current Labels
    text_group = displayio.Group(scale=1, x=10, y=60)
    text = "MT:{:04.1f} F HT:{:04.1f} F".format(motor_temp,heatsink_temp)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)
    

def drawScreen():
    
    global amp_bar
    global testValue1
    
    
    amp_bar.value = testValue1
    testValue1 = (testValue1 + 10) % 110
    print(testValue1)
    
    #keeping old screen code for now, below return
    return
    #Draw odometer label
    text_group = displayio.Group(scale=1, x=2, y=8)
    text = "TRIP:{:05.1f}".format(odometer)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-4] = (text_group)
    
    # Draw Speed/effecency Label
    text_group = displayio.Group(scale=1, x=2, y=27)
    text = "MPH: {:04.1f}".format(mph)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-3] = (text_group)

    # Draw Effecency Label
    text_group = displayio.Group(scale=1, x=2, y=46)
    text = "Amp: {:04.1f}".format(current)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-2] = (text_group)

    # Draw voltage/current Labels
    text_group = displayio.Group(scale=1, x=10, y=60)
    text = "MT:{:04.1f} F HT:{:04.1f} F".format(motor_temp,heatsink_temp)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-1] = (text_group)
    
    
def _shaune_theCAN_isfull():
    '''Checks if the CAN is full'''
    global listener
    message_count = listener.in_waiting()
    if message_count >300:
        mcp._unread_message_queue.clear()
        

def canListener():
    
    global listener
    global odometer
    global motor_temp
    global heatsink_temp
    global mph
    global current
    
    drawtime = time.time()
    sendtime = time.time()
    
    while True:     
        with mcp.listen(timeout=0) as listener:
            if (time.time()-drawtime>0.05):
                    drawScreen()
                    drawtime=time.time()
            
            if (time.time()-sendtime>1):
                uart.write(struct.pack('<fffff',odometer,motor_temp,heatsink_temp,mph,current))
                sendtime=time.time()

            
            _shaune_theCAN_isfull()
            
            
            #Here starts where we do the CAN things
            message_count = listener.in_waiting()
            #print("message count = {}".format(message_count),end = '\n')
            if message_count == 0:

                continue
            
            next_message = listener.receive()
            message_num = 0

            
            while not next_message is None:
            
                if (time.time()-drawtime>0.05):
                    drawScreen()
                    drawtime=time.time()
            

                message_num += 1
                            
                if next_message.id == 0x40E:
                    holder = struct.unpack('<ff', next_message.data)
                    odometer = holder[0]/1609.344
                            # Recieve tempetaure from heat sink and motor
                            
                if next_message.id == 0x40B:
                    #unpack and print the message
                    holder = struct.unpack('<ff',next_message.data)
                    motor_temp = holder[0]
                    heatsink_temp = holder[1]
                    motor_temp = motor_temp * (9/5) + 32 #convert celscisus to farenheight
                    heatsink_temp = heatsink_temp * (9/5) + 32
                    print("Message From: {}: [Motor Temp = {}; Heat Sink = {}]".format(hex(next_message.id),motor_temp,heatsink_temp))
                
                if next_message.id == 0x403:
                    #unpack and print the message
                    holder = struct.unpack('<ff',next_message.data)
                    rpm = holder[0]
                    mph = rpm*tire_diameter*math.pi*60*1/(12*5280)
                    #print("Message From: {}: [rpm = {}; mph = {}]".format(hex(next_message.id),rpm,mph))

                if next_message.id == 0x402:
                #unpack and print the message
                    holder = struct.unpack('<ff',next_message.data)
                    voltage = holder[0]
                    current = holder[1]
                    

                
                if next_message == 0x401:
                    DCU_timeout = time.monotonic_ns() - prevDCU_time
                    prevDCU_time = time.monotonic_ns()
                    
                    
                    
                next_message = listener.receive()

def frontcover():
    #Draw Frontfilm over our text
    bitmap = displayio.OnDiskBitmap("resources/DriverScreen.bmp")
    bitmap.pixel_shader.make_transparent(0)
    frontfilm = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
    splash.append(frontfilm)

def main():
    
    
    initScreen()
    frontcover()
    
    time.sleep(0.2)

    #loops continuously checking for can messages after this, also updates the screen.
    canListener()
    

main()
    



