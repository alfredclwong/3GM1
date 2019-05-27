#include <Wire.h>
#include <SoftwareSerial.h>
#include "MAX30100_PulseOximeter.h"
#define REPORTING_PERIOD_MS     1000

// PulseOximeter is the higher level interface to the sensor
// it offers:
//  * beat detection reporting
//  * heart rate calculation
//  * SpO2 (oxidation level) calculation
PulseOximeter pox;

SoftwareSerial BTserial(3, 4); // RX | TX
// NOTE: CHANGED (2,3)->(3,4) SINCE MAX30100.h USES PIN 2
// Connect the HC-06 TX to the Arduino RX on pin 3. 
// Connect the HC-06 RX to the Arduino TX on pin 4 through a voltage divider.

uint32_t tsLastReport = 0;
uint32_t tsElapsed = 0;
char header[] = "{\"name\":\"SP02\",\"labels\":[\"Heart_rate\",\"Oxygen\"],\"data_units\":[\"bpm\",\"%\"],\"data_range\":[[0,200],[90,100]],\"sampling_rate\":1,\"Version\":\"1.0_Alpha\"}";

// Callback (registered below) fired when a pulse is detected
void onBeatDetected()
{
    //Serial.println("Beat!");
}
 
void setup()
{
    Serial.begin(9600);
    //Serial.setTimeout(1000); // attempt at fixing the initial non-responsiveness - didn't fix
    
    // HC-06 default serial speed is 9600
    BTserial.begin(9600);  
    //BTserial.setTimeout(1000);
 
    //Serial.print("Initializing pulse oximeter..");
 
    // Initialize the PulseOximeter instance
    // Failures are generally due to an improper I2C wiring, missing power supply
    // or wrong target chip
    if (!pox.begin()) {
        //Serial.println("FAILED");
    } else {
        //Serial.println("SUCCESS");
    }
 
    // The default current for the IR LED is 50mA and it could be changed
    //   by uncommenting the following line. Check MAX30100_Registers.h for all the
    //   available options.
    pox.setIRLedCurrent(MAX30100_LED_CURR_24MA);
 
    // Register a callback for the beat detection
    pox.setOnBeatDetectedCallback(onBeatDetected);
    tsLastReport = millis();
}
 
void loop()
{
  // Make sure to call update as fast as possible
  pox.update();
  
  /*
   * 1. Wait for setup signal from Pi
   * 2. Send header to Pi
   *  - device name: "SpO2 sensor"
   *  - data labels: ["Heart rate", "SpO2"]
   *  - units: ["bpm", "%"]
   *  - sampling rate: 1 Hz
   *  - expected data range: [[0, 220], [0, 100]]
   * 3. Respond to Pi requests
   *  - request data
   *  - stop?
   */
  
  if (Serial.available()) {
    char incomingByte = Serial.read();
    switch (incomingByte) {
      case 'A':
        Serial.println(header);
        break;
      case 'B':
        Serial.print("{\"Heart_rate\":");
        Serial.print(pox.getHeartRate());
        Serial.print(",\"Oxygen\":");
        Serial.print(pox.getSpO2());
        Serial.print("}\n");
        break;
    }
  }

  if (BTserial.available()) {
    char incomingByte = BTserial.read();
    switch (incomingByte) {
      case 'A':
        BTserial.println(header);
        break;
      case 'B':
        BTserial.print("{\"Heart_rate\":");
        BTserial.print(pox.getHeartRate());
        BTserial.print(",\"Oxygen\":");
        BTserial.print(pox.getSpO2());
        BTserial.print("}\n");
        break;
    }
  }
}
