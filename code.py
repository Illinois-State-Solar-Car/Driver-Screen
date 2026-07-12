'''
Last Edit: 06/30/26
By: Jason Bliss for the GUI

The Following code is for the driver display

Please make sure to include the following in the lib folder:
adafruit_display_text
adafruit_mcp2515
adafruit_ssd1325.py
adafruit_display_shapes
adafruit_progressbar


TODO:
    Maybe Add Odometer Back
    Make .bmp actually match the bars
'''


#--------------Imports-------------------------#

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
from adafruit_progressbar.progressbar import HorizontalProgressBar
from adafruit_display_shapes.arc import Arc

#--------------Initalization stuff--------------------------#

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
display = adafruit_ssd1325.SSD1325(display_bus, width=WIDTH, height=HEIGHT, rotation=180)
display.brightness = 1.0



startTime = time.time()
# Make the display context
splash = displayio.Group()
display.root_group = splash

#--------------Displayign the Startup Screen For a Bit--------------------------#
text = "    SOLAR CAR ISU\n    Driver Screen\n\nYou Just Got Dunham'd"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
text_width = text_area.bounding_box[2] * FONTSCALE
text_group = displayio.Group(
    scale=FONTSCALE,
    x=display.width // 2 - text_width // 2,
    y=int(display.height / 6)
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

#--------------Progress Bar Initalization Items--------------#

#defining some stuff for the progress bars to be used elsewhere, mainly for test code, not running on actual car.

#testValue1 = 0
#mph_test_value = 0


#Progress bar rendering value variables
amp_rendered_value = 0
motor_temp_rendered_value = 0
heatsink_temp_rendered_value = 0
mph_rendered_value = 0

#for ideal positioning, Position y + Size y = 64 for these to keep them uniform.
amp_bar = VerticalProgressBar(
    (30, 30),#position
    (20, 34),#size
    bar_color=0xFFFFFF,
    outline_color = 0x000000,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 0,
    min_value = 0,
    max_value = 55
)


motor_temp_bar = VerticalProgressBar(
    (62, 30),#position
    (20, 34),#size
    bar_color=0xFFFFFF,
    outline_color = 0x000000,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 70,
    min_value = 32,
    max_value = 110
)

heat_sink_bar = VerticalProgressBar(
    (94, 30),#position
    (20, 34),#size
    bar_color=0xFFFFFF,
    outline_color = 0x000000,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 70,
    min_value = 32,
    max_value = 110
)


#The MPH progress bar:
#Broken into two since it's a curved and then a straight section
mph_bar = Arc(
    x=64,
    y=64,
    radius=65,
    angle=0,
    direction=180,
    segments=22,
    arc_width=16,
    outline=0x000000,
    fill=0xFFFFFF
)

mph_bar2 = HorizontalProgressBar(
    position=(61, 2),#position
    size=(330, 14),#size I'm maing absurdly big so that the jump from 50 to 70 fills more
    bar_color=0xFFFFFF,
    outline_color = 0x000000,
    fill_color = 0x000000,
    border_thickness = 0,
    margin_size = 0,
    value = 0
    
)

#warning text

ampWarningLabels = displayio.Group(scale=1, x=25, y=52)
ampWarningLabel = label.Label(terminalio.FONT, text="!", color=0xFFFFFF)
ampWarningLabels.append(ampWarningLabel)  # Subgroup for text scaling

motorWarningLabels = displayio.Group(scale=1, x=57, y=52)
motorWarningLabel = label.Label(terminalio.FONT, text="!", color=0xFFFFFF)
motorWarningLabels.append(motorWarningLabel)  # Subgroup for text scaling

heatsinkWarningLabels = displayio.Group(scale=1, x=89, y=52)
heatsinkWarningLabel = label.Label(terminalio.FONT, text="!", color=0xFFFFFF)
heatsinkWarningLabels.append(heatsinkWarningLabel)  # Subgroup for text

#Helper variable for flashing the exclamation marks when a value is too high
warningFlashing = True


#MPH label
mphLabelGroup = displayio.Group(scale=1, x=114, y=8)
mphLabel = label.Label(terminalio.FONT, text="0", color=0xFFFFFF)
mphLabelGroup.append(mphLabel)  # Subgroup for text scaling

#Other Labels
ampLabelGroup = displayio.Group(scale=1, x=38, y=26)
ampLabel = label.Label(terminalio.FONT, text="A", color=0xFFFFFF)
ampLabelGroup.append(ampLabel)  # Subgroup for text scaling

mtLabelGroup = displayio.Group(scale=1, x=67, y=26)
mtLabel = label.Label(terminalio.FONT, text="MT", color=0xFFFFFF)
mtLabelGroup.append(mtLabel)  # Subgroup for text scaling

htLabelGroup = displayio.Group(scale=1, x=97, y=26)
htLabel = label.Label(terminalio.FONT, text="HT", color=0xFFFFFF)
htLabelGroup.append(htLabel)  # Subgroup for text scaling
    


#--------------Screen Drawing Helper Functions--------------------------#

def clamp(value, min, max):
    if value > max:
        return max
    if value < min:
        return min
    return value

def IsInNormalRange(value, min, max):
    return (not ((value > max) or (value < min)))

def initScreen():
    global amp_bar
    global motor_temp_bar
    global heat_sink_bar
    global mph_bar
    
    
    splash.append(amp_bar)
    splash.append(motor_temp_bar)
    splash.append(heat_sink_bar)
    splash.append(mph_bar)
    splash.append(mph_bar2)
    
    splash.append(ampWarningLabels)
    splash.append(motorWarningLabels)
    splash.append(heatsinkWarningLabels)
    
    splash.append(mphLabelGroup)
    splash.append(ampLabelGroup)
    splash.append(mtLabelGroup)
    splash.append(htLabelGroup)
    
    
    
    #keeping old screen code for now, located below return
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
    global motor_temp_bar
    global heat_sink_bar
    global mph_bar
    global mph_bar2
    
    global ampWarningLabels
    global motorWarningLabels
    global heatsinkWarningLabels
    global warningFlashing
    
    global testValue1
    global mph_test_value
    
    global odometer
    global mph
    global current
    global motor_temp
    global heatsink_temp
    
    display.auto_refresh = False
    
    
    #Testing to see if warnings are true
    ampWarning = not IsInNormalRange(current, 0, 50)
    motorTempWarning = not IsInNormalRange(motor_temp, 37, 105)
    heatSinkTempWarning = not IsInNormalRange(heatsink_temp, 37, 105)
    mphWarning = not IsInNormalRange(mph, 0, 70)
    
    if ampWarning:
        ampWarningLabels.hidden = warningFlashing
    else:
        ampWarningLabels.hidden = True
    
    if motorTempWarning:
        motorWarningLabels.hidden = warningFlashing
    else:
        motorWarningLabels.hidden =True
        
    if heatSinkTempWarning:
        heatsinkWarningLabels.hidden = warningFlashing
    else:
        heatsinkWarningLabels.hidden = True
        
    if mphWarning:
        if warningFlashing:
            mph_bar.fill = 0xFFFFFF
            mph_bar2.bar_color = 0xFFFFFF
        else:
            mph_bar.fill = 0x000000
            mph_bar2.bar_color = 0x000000
    else:
        mph_bar.fill = 0xFFFFFF
        mph_bar2.bar_color = 0xFFFFFF
    
    warningFlashing = not warningFlashing
    
    
    amp_rendered_value = clamp(current, 0, 55)
    motor_temp_rendered_value = clamp(motor_temp, 32, 110)
    heatsink_temp_rendered_value = clamp(heatsink_temp, 32, 110)
    mph_rendered_value = clamp(mph, 0, 65)
    
    amp_bar.value = amp_rendered_value
    motor_temp_bar.value = motor_temp_rendered_value
    heat_sink_bar.value = heatsink_temp_rendered_value
    
    #more complicated since is composed of two bars combined into one.
    
    mphLabel.text = str(mph)
    
    
    if mph <= 50:
        mph_bar.angle = -mph_rendered_value * 1.75#magic number to make it look nicer.
        mph_bar2.value = 0
    else: # above 50, use second bar
        mph_bar.angle = -50 * 1.75
        mph_bar2.value = mph_rendered_value - 50
    

    
    #keeping old screen code for now, located below return
    display.auto_refresh = True
    
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
    
def frontcover():
    #Draw Frontfilm over our text
    bitmap = displayio.OnDiskBitmap("resources/DriverScreen.bmp")
    bitmap.pixel_shader.make_transparent(0)
    frontfilm = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
    splash.append(frontfilm)
    
    
#--------------Can Helper Functions--------------------------#
def _shaune_theCAN_isfull():
    '''Checks if the CAN is full'''
    global listener
    message_count = listener.in_waiting()
    if message_count >300:
        mcp._unread_message_queue.clear()
        

#Loops continuously. As such also contains all calls for drawing and such. You can think of this function as main since main mostly does setup then calls this.
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



def main():
    
    initScreen()
    frontcover()
    
    time.sleep(0.2)

    #loops continuously checking for can messages after this, also updates the screen.
    canListener()
    

main()
    




