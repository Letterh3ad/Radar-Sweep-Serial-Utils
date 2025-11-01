#include <Servo.h>

const int trigPin = 9;     // Ultrasonic trigger
const int echoPin = 10;    // Ultrasonic echo
const int ledPin  = 13;    // Onboard LED
const int servoPin = 6;    // Servo control

Servo servo;
long duration;
float distanceCM;
int angle = 0;
int direction = 1;         // 1 = forward, -1 = backward
const int threshold = 30;  // LED turns on if closer than (cm)

void setup() {
  Serial.begin(9600);
  servo.attach(servoPin);
  servo.write(angle);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(ledPin, OUTPUT);

  Serial.println("Ultrasonic Radar Initialized");
}

void loop() {
  // Trigger ultrasonic pulse
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Measure echo duration (us)
  duration = pulseIn(echoPin, HIGH, 30000UL); // 30ms timeout

  //Calculations us to CM
  if (duration > 0) {
    distanceCM = (duration * 0.0343) / 2.0;
    Serial.print(distanceCM);
    Serial.print(",");
    Serial.println(angle);

    // LED feedback
    digitalWrite(ledPin, (distanceCM < threshold) ? HIGH : LOW);
  } else {
    Serial.print("No echo at angle: ");
    Serial.println(angle);
  }

  // Move servo for sweep
  angle += direction;
  if (angle >= 180 || angle <= 0) {
    direction = -direction;
    delay(100);
  }

  servo.write(angle);
  delay(40);
}
