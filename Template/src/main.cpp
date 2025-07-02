#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

#define POT_PIN 35

const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* mqtt_server = "broker.hivemq.com";

const char* topicRaw = "/indobot/p/pot/raw";
const char* topicVolt = "/indobot/p/pot/voltage";

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsgTime = 0;

float floatMap(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

void setup_wifi() {
  Serial.print("Conectando a ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectada, IP:");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conexión MQTT...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("conectado");
    } else {
      Serial.print("falló, rc=");
      Serial.print(client.state());
      Serial.println(" — reintentando en 5s");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(POT_PIN, INPUT);
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
  unsigned long now = millis();
  if (now - lastMsgTime > 1000) {
    lastMsgTime = now;
    int analogValue = analogRead(POT_PIN);
    float voltage = floatMap(analogValue, 0, 4095, 0.0, 3.3);

    char bufRaw[8];
    char bufVolt[16];
    snprintf(bufRaw, sizeof(bufRaw), "%d", analogValue);
    snprintf(bufVolt, sizeof(bufVolt), "%.2f", voltage);

    Serial.print("Pot raw: ");
    Serial.print(bufRaw);
    Serial.print(" | Voltage: ");
    Serial.println(bufVolt);
  }
}