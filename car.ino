#include <Servo.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

char Move; // | W = Forward | A = Turn Left | S = Backwards | D = Turn Left |
int Speed = 255;

const int IN1 = 7;    //Left
const int IN2 = 8;    //Left

const int IN3 = 2;    //Right
const int IN4 = 12;    //Right

const int Buzz = 11;


void setup() {

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(Buzz, OUTPUT);
  Serial.begin(9600); 
  dht.begin();


}

void loop() {

  if (Serial.available()) {
  Move = Serial.read();
}

  switch (Move)
    {

      case 'w': // Forward
          digitalWrite(IN1, HIGH);
          digitalWrite(IN2, LOW);
          digitalWrite(IN3, HIGH);
          digitalWrite(IN4, LOW);
          delay(10); 
        break;

      case 'a':// Turn Left
        digitalWrite(IN1, LOW);
        digitalWrite(IN2, HIGH);
        digitalWrite(IN3, HIGH);
        digitalWrite(IN4, LOW);
        delay(10); 
        break;

      case 's':// Backwards
        digitalWrite(IN1, LOW);
        digitalWrite(IN2, HIGH);
        digitalWrite(IN3, LOW);
        digitalWrite(IN4, HIGH);
        delay(10); 
        break;

      case 'd':// Turn Right
        digitalWrite(IN1, HIGH);
        digitalWrite(IN2, LOW);
        digitalWrite(IN3, LOW);
        digitalWrite(IN4, HIGH);
        delay(10);
        break;
      
      case 'x'://Stop
        digitalWrite(IN1, LOW);
        digitalWrite(IN2, LOW);
        digitalWrite(IN3, LOW);
        digitalWrite(IN4, LOW);
        digitalWrite(Buzz,LOW);
        delay(10); 
        break;

      case 'b':
        digitalWrite(Buzz,HIGH);
        delay(10); 
        break;
    }
   

   

  static unsigned long lastDHTReadTime = 0;
  const unsigned long DHTInterval = 5000;
  if (millis() - lastDHTReadTime >= DHTInterval) 
  {
    lastDHTReadTime = millis();
    
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (isnan(h) || isnan(t)) {
      Serial.println("Error reading from DHT sensor");
    } 
    
    else 
    {
      Serial.print("Temperature:");
      Serial.print(t);
      Serial.print(",Humidity:");
      Serial.println(h);
    }
  }
}
