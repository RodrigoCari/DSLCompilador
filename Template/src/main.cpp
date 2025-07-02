#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <math.h>

// Pines
const int tempPin = 32;
const int ledPin = 14;
const float BETA = 3950;

// Wi-Fi
const char* ssid     = "Wokwi-GUEST";
const char* password = "";

const char* mqtt_server = "broker.hivemq.com";
const char* topicTemp = "/indobot/p/temp/value";
const char* topicAlert = "/indobot/p/temp/alert";

WiFiClient espClient;
PubSubClient client(espClient);

// Última temperatura publicada
float lastTemperature = -1000.0;

void setup_wifi() {
  Serial.print("Conectando a ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi OK, IP:");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando MQTT...");
    String clientId = "ESP32TempClient-";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("conectado");
    } else {
      Serial.print("falló rc=");
      Serial.print(client.state());
      Serial.println(" reintentando en 5s");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(9600);
  analogReadResolution(10);
  pinMode(tempPin, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) { reconnect(); }
  client.loop();

  int analogValue = analogRead(tempPin);
  float celsius = 1 / (log(1 / (1023. / analogValue - 1)) / BETA + 1.0 / 298.15) - 273.15;

  Serial.print("Temperature: ");
  Serial.print(celsius);
  Serial.println(" °C");

  char bufTemp[8];
  dtostrf(celsius, 1, 2, bufTemp);
  client.publish(topicTemp, bufTemp);

  if (celsius >= 35.0) {
    digitalWrite(ledPin, HIGH);
    client.publish(topicAlert, "ALERTA");
  } else {
    digitalWrite(ledPin, LOW);
    client.publish(topicAlert, "OK");
  }

  delay(1000);
}