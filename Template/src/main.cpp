#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

// Pines
#define gasPin   36
#define ledPin   2

// Wi-Fi
const char* ssid     = "Wokwi-GUEST";
const char* password = "";

const char* mqtt_server = "broker.hivemq.com";
const char* topicGasValue = "/indobot/p/gas/value";
const char* topicGasAlert = "/indobot/p/gas/alert";

WiFiClient espClient;
PubSubClient client(espClient);

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

void callback(char* topic, byte* payload, unsigned int length) {}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando MQTT...");
    String clientId = "ESP32GasSensor-";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("Conectado");
    } else {
      Serial.print("Falló, rc=");
      Serial.print(client.state());
      Serial.println(" reintentando en 5s");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(gasPin, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) { reconnect(); }
  client.loop();

  int gasValue = analogRead(gasPin);
  Serial.print("Gas Sensor Value: ");
  Serial.print(gasValue);

  char bufValue[6];
  snprintf(bufValue, sizeof(bufValue), "%d", gasValue);
  client.publish(topicGasValue, bufValue);

  if (gasValue <= 700) {
    digitalWrite(ledPin, HIGH);
    Serial.println(" --> Danger! Gas leak detected!");
    client.publish(topicGasAlert, "DANGER");
  } else {
    digitalWrite(ledPin, LOW);
    Serial.println(" --> Environment safe");
    client.publish(topicGasAlert, "SAFE");
  }

  delay(1000);
}