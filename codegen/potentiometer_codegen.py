import json
from codegen.base_codegen import BaseCodeGenerator

class PotentiometerCodeGenerator(BaseCodeGenerator):
    def __init__(self, tokens):
        super().__init__(tokens)
        self.topics = {}
        self.interval = 1000
        self.broker = ""
        self.cpp_lines = []

    def generate(self):
        self.parse_tokens()
        self.emit_headers()
        self.emit_loop_start()
        self.emit_loop_end()
        self.generate_diagram_json()
        return "\n".join(self.cpp_lines)

    def parse_tokens(self):
        while self.index < len(self.tokens):
            token_type, value = self.current()

            if token_type == 308:  # CONNECT
                self.index += 2
                _, broker = self.current(); self.index += 1
                self.broker = broker.strip('"')
                self.index += 2

            elif token_type == 300:  # TOPIC
                self.index += 1
                _, name = self.current(); self.index += 1
                self.index += 1
                _, path = self.current(); self.index += 1
                self.topics[name] = path.strip('"')
                self.index += 1

            elif token_type == 303:  # TIMER
                self.index += 3
                _, val = self.current(); self.index += 1
                try:
                    self.interval = int(val)
                except ValueError:
                    raise ValueError(f"Se esperaba un número para el intervalo, pero se encontró: {val}")
                self.index += 2
                while self.current()[0] in [302, 315]:
                    while self.current()[0] != 270:
                        self.index += 1
                    self.index += 1
                self.index += 1

            else:
                self.index += 1

    def emit_headers(self):
        self.cpp_lines.extend([
            "#include <Arduino.h>",
            "#include <WiFi.h>",
            "#include <PubSubClient.h>",
            "",
            "#define POT_PIN 35",
            "",
            'const char* ssid = "Wokwi-GUEST";',
            'const char* password = "";',
            f'const char* mqtt_server = "{self.broker}";',
            ""
        ])

        for name, topic in self.topics.items():
            if "RAW" in name.upper():
                self.cpp_lines.append(f'const char* topicRaw = "{topic}";')
            elif "VOLT" in name.upper():
                self.cpp_lines.append(f'const char* topicVolt = "{topic}";')

        self.cpp_lines.extend([
            "",
            "WiFiClient espClient;",
            "PubSubClient client(espClient);",
            "unsigned long lastMsgTime = 0;",
            "",
            "float floatMap(float x, float in_min, float in_max, float out_min, float out_max) {",
            "  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;",
            "}",
            "",
            "void setup_wifi() {",
            "  Serial.print(\"Conectando a \");",
            "  Serial.println(ssid);",
            "  WiFi.mode(WIFI_STA);",
            "  WiFi.begin(ssid, password);",
            "  while (WiFi.status() != WL_CONNECTED) {",
            "    delay(500);",
            "    Serial.print(\".\");",
            "  }",
            "  Serial.println(\"\\nWiFi conectada, IP:\");",
            "  Serial.println(WiFi.localIP());",
            "}",
            "",
            "void callback(char* topic, byte* payload, unsigned int length) {}",
            "",
            "void reconnect() {",
            "  while (!client.connected()) {",
            "    Serial.print(\"Intentando conexión MQTT...\");",
            "    String clientId = \"ESP32Client-\";",
            "    clientId += String(random(0xffff), HEX);",
            "    if (client.connect(clientId.c_str())) {",
            "      Serial.println(\"conectado\");",
            "    } else {",
            "      Serial.print(\"falló, rc=\");",
            "      Serial.print(client.state());",
            "      Serial.println(\" — reintentando en 5s\");",
            "      delay(5000);",
            "    }",
            "  }",
            "}",
            "",
            "void setup() {",
            "  pinMode(POT_PIN, INPUT);",
            "  Serial.begin(115200);",
            "  setup_wifi();",
            "  client.setServer(mqtt_server, 1883);",
            "  client.setCallback(callback);",
            "}"
        ])

    def emit_loop_start(self):
        self.cpp_lines.extend([
            "",
            "void loop() {",
            "  if (!client.connected()) reconnect();",
            "  client.loop();",
            "  unsigned long now = millis();",
            f"  if (now - lastMsgTime > {self.interval}) {{",
            "    lastMsgTime = now;",
            "    int analogValue = analogRead(POT_PIN);",
            "    float voltage = floatMap(analogValue, 0, 4095, 0.0, 3.3);",
            "",
            "    char bufRaw[8];",
            "    char bufVolt[16];",
            "    snprintf(bufRaw, sizeof(bufRaw), \"%d\", analogValue);",
            "    snprintf(bufVolt, sizeof(bufVolt), \"%.2f\", voltage);",
            ""
        ])
        if "RAW" in (k.upper() for k in self.topics.keys()):
            self.cpp_lines.append("    client.publish(topicRaw, bufRaw);")
        if "VOLT" in (k.upper() for k in self.topics.keys()):
            self.cpp_lines.append("    client.publish(topicVolt, bufVolt);")
        self.cpp_lines.extend([
            "    Serial.print(\"Pot raw: \");",
            "    Serial.print(bufRaw);",
            "    Serial.print(\" | Voltage: \");",
            "    Serial.println(bufVolt);",
            "  }"
        ])

    def emit_loop_end(self):
        self.cpp_lines.append("}")

    def generate_diagram_json(self):
        diagram = {
            "version": 1,
            "author": "Baca Pikiran",
            "editor": "wokwi",
            "parts": [
                { "type": "board-esp32-devkit-c-v4", "id": "esp", "top": 48, "left": 62.44, "attrs": {} },
                { "type": "wokwi-potentiometer", "id": "pot1", "top": -39.7, "left": -86.6, "attrs": {} }
            ],
            "connections": [
                [ "esp:TX", "$serialMonitor:RX", "", [] ],
                [ "esp:RX", "$serialMonitor:TX", "", [] ],
                [ "pot1:SIG", "esp:35", "green", [ "v96", "h18.8" ] ],
                [ "esp:3V3", "pot1:VCC", "green", [ "h-105.45" ] ],
                [ "pot1:GND", "esp:GND.2", "black", [ "v28.8", "h220.8", "v-28.8" ] ]
            ],
            "dependencies": {}
        }
        with open("Template/diagram.json", "w") as f:
            json.dump(diagram, f, indent=2)
        print("[GENERATOR] Archivo diagram.json generado para POTENTIOMETER.")
