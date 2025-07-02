#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

// Pines
const int pirPin = 2;
const int ledPin = 5;

// Wi-Fi
const char* ssid     = "Wokwi-GUEST";
const char* password = "";

const char* mqtt_server = "broker.hivemq.com";
const char* topicState = "/indobot/p/pir/state";
const char* topicStatus = "/indobot/p/pir/status";

WiFiClient espClient;
PubSubClient client(espClient);

// Guarda el último estado para publicar solo cuando cambie
int lastPirState = LOW;

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
    String clientId = "ESP32Client-";
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

void callback(char* topic, byte* payload, unsigned int length) {
  // No se usa
}

void setup() {
  pinMode(pirPin, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  int pirState = digitalRead(pirPin);
  if (pirState != lastPirState) {
    lastPirState = pirState;

    digitalWrite(ledPin, pirState == HIGH ? HIGH : LOW);

    char bufState[2];
    char bufStatus[12];
    snprintf(bufState, sizeof(bufState), "%d", pirState);
    snprintf(bufStatus, sizeof(bufStatus), pirState == HIGH ? "MOTION" : "NO_MOTION");

    client.publish(topicState, bufState);
    client.publish(topicStatus, bufStatus);

    Serial.print("PIR raw: ");
    Serial.print(bufState);
    Serial.print(" | Estado: ");
    Serial.println(bufStatus);
  }

  delay(1000);
}