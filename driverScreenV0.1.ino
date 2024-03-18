/*
 * LAST UPDATE: 3/18/24
 * V0.1
 * Still need to work on displaying and ensuring the can information comes in correctly
 * Code for the driver display boards on the ISU solar car
 * Used for:
 *  - Displaying data to the driver for speed, battery capacity,
 *    array input, and so much more (i forgot what else there is)
 *  - take data in from motor controller can as well as battery box
 *  
 */

/*
 * Pin Info
 * Pin 1 -> ground
 * Pin 2 -> 3v supply
 * Pin 4 (DC) -> digital 8 (level shifter)
 * Pin 7 (SCLK) -> digital 16 (level shifter)
 * Pin 8 (DIN)(MOSI) -> digital 15 (level shifter)
 * Pin 15 (CS) -> digital 10 (level shifter)
 * Pin 16 (RST) -> digital 9 (level shifter)
 * 
 * Power the HC4050 level shifter by connecting pin 1 to 3v and pin 8 to the ground
 */


//can imports
#include <mcp_can.h>
#include <mcp_can_dfs.h>

//can setup
const int SPI_CS_PIN = 17; //CANBed V1
// const int SPI_CS_PIN = 3;            // CANBed M0
// const int SPI_CS_PIN = 9;            // CAN Bus Shield
//I'm not sure which can we have so here we go

MCP_CAN CAN(SPI_CS_PIN); //set CS pin

//display imports
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1305.h>

//OLED setup
#define OLED_CLK 16
#define OLED_MOSI 15
#define OLED_CS 10
#define OLED_DC 8
#define OLED_RESET 9

//set up the display
Adafruit_SSD1305 display(128, 64, OLED_MOSI, OLED_CLK, OLED_DC, OLED_RESET, OLED_CS);

//does stuff for display
#define NUMFLAKES 10
#define XPOS 0
#define YPOS 1
#define DELTAY 2 //does this look like someone spelled delay wrong? yes but either it is misspelled 4 times in the example or it is intentional so I'm going to assume intentional

#define LOGO16_GLCD_HEIGHT 16
#define LOGO16_GLCD_WIDTH 16

//NONGMO code
static const unsigned char PROGMEM logo16_glcd_bmp[] =
{ B00000000, B11000000,
  B00000001, B11000000,
  B00000001, B11000000,
  B00000011, B11100000,
  B11110011, B11100000,
  B11111110, B11111000,
  B01111110, B11111111,
  B00110011, B10011111,
  B00011111, B11111100,
  B00001101, B01110000,
  B00011011, B10100000,
  B00111111, B11100000,
  B00111111, B11110000,
  B01111100, B11110000,
  B01110000, B01110000,
  B00000000, B00110000 };


//variable initializations (probably spelled that wrong) 

float lowTemp =   20;
float highTemp =  20;
float avgTemp =    20;

int tire_diameter = 22; //inches 
float mph = 0;
float voltage = 0;
float current = 0;
float efficiency = 0;
float heatsink_temp = 0;
float motor_temp = 0;
float DCU_timeout = 0;
//float prevDCU_time = time.monotonic_ns();

//void can_is_filled(){
//  do can is filled stuff
//}

//set up stuff
void setup() {
  // put your setup code here, to run once:
//  Serial.begin(9600);
//  while(!Serial) delay(100);
//  Serial.println("SSD1305 OLED test");
//
//  if(!display.begin(0x3c)){
//    Serial.println("Unable to initialize OLED");
//    while(1) yield();
//  }

  Serial.begin(115200);
  while(!Serial);
  while(CAN_OK != CAN.begin(CAN_500KBPS)){
    Serial.println("CANBUS FAILED!");
    delay(100);
  }
  Serial.println("CANBUS OK!");
}

float bytesToFloat(byte* byteArr){
  float floatVal;
  memcpy(&floatVal, byteArr, sizeof(float));
  return floatVal;
}





void loop() {
  // put your main code here, to run repeatedly:

  //get the can data
  unsigned char len = 0;
  unsigned char buf[8];

  //receive can messages
  if(CAN_MSGAVAIL == CAN.checkReceive()){
    CAN.readMsgBuf(&len, buf); //read the message buffer
    unsigned long canId = CAN.getCanId(); //get the canID
    
    if(canId == 0x403){ //if the can is sending speeeeeeed info
      byte* subArr = (byte*) malloc (4 * sizeof(byte)); //set up a byte array the size of the first 4 bytes (RPM)
      
      memcpy(subArr, buf, 4); //copy the first 4 bytes of the array
      float rpm = bytesToFloat(subArr); //turn the bytes containing RPM into a float value for RPM
      mph = (rpm * tire_diameter * 3.14 * 60) / (12 * 5280); //turn RPM into mph 
    }
    else if(canId == 0x40B){ //if the can is sending motor_temp and heatsink_temp info
      byte* motorArr = (byte*) malloc (4 * sizeof(byte));
      byte* heatsinkArr = (byte*) malloc (4 * sizeof(byte));

      memcpy(motorArr, buf, 4); //copy the first 4 bytes into motorArr
      memcpy(heatsinkArr, buf + 4, 8); //copy the next 4 bytes into heatsinkArr

      motor_temp = bytesToFloat(motorArr);
      heatsink_temp = bytesToFloat(heatsinkArr);
    }
    else if(canId == 0x402){ //if we are getting volts and amps from the motor controller
      byte* voltArr = (byte*) malloc (4 * sizeof(byte));
      byte* ampArr = (byte*) malloc (4 * sizeof(byte));

      memcpy(voltArr, buf, 4); //copy the bytes into voltArr
      memcpy(ampArr, buf + 4, 8); //copy bytes into ampArr

      voltage = bytesToFloat(voltArr); //turn the bytes into floats
      current = bytesToFloat(ampArr);
    }

    
  }




  

}
