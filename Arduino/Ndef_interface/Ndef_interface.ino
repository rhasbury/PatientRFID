
#include <Wire.h>
#include <PN532_I2C.h>
#include <PN532.h>
#include <NfcAdapter.h>
#include <avr/wdt.h>


PN532_I2C pn532_i2c(Wire);
NfcAdapter nfc = NfcAdapter(pn532_i2c);

String inputString = "";         // a string to hold incoming data
//String tempString = "";         // a string to hold outgoing data
boolean stringComplete = false;  // whether the string is complete


void setup(void) {
    wdt_disable();
    Serial.begin(115200);
    Serial.println("NDEF Reader");
    inputString.reserve(2000);
//    tempString.reserve(200);
    nfc.begin();
    wdt_enable(WDTO_8S);

}

void loop(void) {
    int success = 0;
    int colon = 0;
    if (stringComplete) {
      //Serial.println(inputString);
      // clear the string:
      
      if(inputString.indexOf("write_tag") >= 0){
        // dig info out of string and write to tag 
        // String format example for write command  "write_tag:thistextgetswrittentotag"
        if (nfc.tagPresent()) {
             success = nfc.clean();
             success = nfc.format();
             NdefMessage message = NdefMessage();
             colon = inputString.indexOf(":");
             if(colon >= 0){
                message.addTextRecord(inputString.substring(colon+1)); 
                
                success = nfc.write(message);
                if(success){ Serial.println("Success");}; 
             }
             
           }
     
      }
  
      
      if(inputString.indexOf("read_tag") >= 0){
        // Print tag information back to serial      
        if (nfc.tagPresent(100))
        {
          NfcTag tag = nfc.read();
          //tag.print();
          if(tag.hasNdefMessage()){
            NdefMessage message = tag.getNdefMessage();
            NdefRecord record = message.getRecord(0);
            byte payloadArray[record.getPayloadLength()];
            record.getPayload(payloadArray);       
            //String tempstring = String(payloadArray);
            Serial.write("Sucess:"); 
            Serial.write(payloadArray+3, record.getPayloadLength()-3);             
           }
          
        }
        else
        {
          Serial.println("no tag");      
        }
           
      }
         
      inputString = "";
      stringComplete = false;
  }
  
  delay(100);
  wdt_reset();
}


/*
  SerialEvent occurs whenever a new data comes in the
 hardware serial RX.  This routine is run between each
 time loop() runs, so using delay inside loop can delay
 response.  Multiple bytes of data may be available.
 */
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n' or inChar == ';') {
      stringComplete = true;
    }
  }
}


