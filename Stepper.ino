#define DIR_PIN   5
#define STEP_PIN  2
#define EN_PIN    8

const int STEP_DELAY = 1000;  

long curSteps = 0;
String cmdBuf;

void setup() {
  pinMode(DIR_PIN, OUTPUT);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);
  digitalWrite(EN_PIN, LOW);    

  Serial.begin(115200);
  Serial.println("# Ready, curSteps=0");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r' || c == '\n') {
       
      String s = cmdBuf;
      s.trim();
      cmdBuf = "";

     
      long n = s.toInt();
      Serial.println("[CMD] " + s);

      if (n != 0) {
        bool dir = (n > 0);
        digitalWrite(DIR_PIN, dir ? HIGH : LOW);

        long stepsToMove = abs(n);
        for (long i = 0; i < stepsToMove; i++) {
          digitalWrite(STEP_PIN, HIGH);
          delayMicroseconds(STEP_DELAY);
          digitalWrite(STEP_PIN, LOW);
          delayMicroseconds(STEP_DELAY);
          curSteps += dir ? 1 : -1;
        }
        Serial.println(curSteps);
      }
      else {
       
        Serial.println(curSteps);
      }
    }
    else {
      cmdBuf += c;
    }
  }
}
