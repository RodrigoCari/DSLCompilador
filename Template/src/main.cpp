#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

#define Trigger 2
#define Echo    4
#define ledPin  13

long t;
long d;

const char* ssid     = "Wokwi-GUEST";
const char* password = "";
const char* mqtt_server = "broker.hivemq.com";

const char* topicDistance = "/indobot/p/ultrasonic/distance";
const char* topicAlert = "/indobot/p/ultrasonic/alert";

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
    String clientId = "ESP32Ultrasonic-";
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
  pinMode(Trigger, OUTPUT);
  pinMode(Echo, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(Trigger, LOW);
  digitalWrite(ledPin, LOW);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  digitalWrite(Trigger, HIGH);
  delayMicroseconds(10);
  digitalWrite(Trigger, LOW);

  t = pulseIn(Echo, HIGH);
  d = t / 59 + 1;

  Serial.print("Distancia: ");
  Serial.print(d);
  Serial.println(" cm");

  char bufDist[8];
  snprintf(bufDist, sizeof(bufDist), "%ld", d);
  client.publish(topicDistance, bufDist);

  if (d < 40) {
    digitalWrite(ledPin, HIGH);
    client.publish(topicAlert, "NEAR");
  } else {
    digitalWrite(ledPin, LOW);
    client.publish(topicAlert, "CLEAR");
  }
  delay(1000);
}