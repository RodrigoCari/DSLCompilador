import json
from codegen.base_codegen import BaseCodeGenerator

class UltrasonicCodeGenerator(BaseCodeGenerator):
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
                self.index += 2  # skip CONNECT (
                _, broker = self.current(); self.index += 1
                self.broker = broker.strip('"')
                self.index += 2  # skip , NUM )
                self.expect(270)  # )

            elif token_type == 300:  # TOPIC
                self.index += 1
                _, name = self.current(); self.index += 1
                self.expect(269)  # (
                _, path = self.current(); self.index += 1
                self.topics[name] = path.strip('"')
                self.expect(270)  # )

            elif token_type == 303:  # TIMER
                self.index += 1  # TIMER
                self.index += 1  # ID
                self.expect(269)  # (
                _, val = self.current(); self.index += 1  # NUM
                self.interval = int(val)
                self.expect(270)  # )
                self.expect(275)  # {
                while self.current()[0] in [302, 315]:  # PUBLISH, PRINT
                    self.index += 1
                    while self.current()[0] != 270:
                        self.index += 1
                    self.index += 1  # skip )
                self.expect(276)  # }

            else:
                self.index += 1

    def emit_headers(self):
        self.cpp_lines.extend([
            "#include <Arduino.h>",
            "#include <WiFi.h>",
            "#include <PubSubClient.h>",
            "",
            "#define Trigger 2",
            "#define Echo    4",
            "#define ledPin  13",
            "",
            "long t;",
            "long d;",
            "",
            "const char* ssid     = \"Wokwi-GUEST\";",
            "const char* password = \"\";",
            f'const char* mqtt_server = \"{self.broker}\";',
            ""
        ])

        for name, topic in self.topics.items():
            if "DISTANCE" in name.upper():
                self.cpp_lines.append(f'const char* topicDistance = "{topic}";')
            elif "ALERT" in name.upper():
                self.cpp_lines.append(f'const char* topicAlert = "{topic}";')

        self.cpp_lines.extend([
            "",
            "WiFiClient espClient;",
            "PubSubClient client(espClient);",
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
            "  Serial.println(\"\\nWi-Fi OK, IP:\");",
            "  Serial.println(WiFi.localIP());",
            "}",
            "",
            "void callback(char* topic, byte* payload, unsigned int length) {}",
            "",
            "void reconnect() {",
            "  while (!client.connected()) {",
            "    Serial.print(\"Intentando MQTT...\");",
            "    String clientId = \"ESP32Ultrasonic-\";",
            "    clientId += String(random(0xffff), HEX);",
            "    if (client.connect(clientId.c_str())) {",
            "      Serial.println(\"Conectado\");",
            "    } else {",
            "      Serial.print(\"Fall\u00f3, rc=\");",
            "      Serial.print(client.state());",
            "      Serial.println(\" reintentando en 5s\");",
            "      delay(5000);",
            "    }",
            "  }",
            "}",
            "",
            "void setup() {",
            "  Serial.begin(115200);",
            "  pinMode(Trigger, OUTPUT);",
            "  pinMode(Echo, INPUT);",
            "  pinMode(ledPin, OUTPUT);",
            "  digitalWrite(Trigger, LOW);",
            "  digitalWrite(ledPin, LOW);",
            "  setup_wifi();",
            "  client.setServer(mqtt_server, 1883);",
            "  client.setCallback(callback);",
            "}"
        ])

    def emit_loop_start(self):
        self.cpp_lines.append("\nvoid loop() {")
        self.cpp_lines.extend([
            "  if (!client.connected()) reconnect();",
            "  client.loop();",
            "",
            "  digitalWrite(Trigger, HIGH);",
            "  delayMicroseconds(10);",
            "  digitalWrite(Trigger, LOW);",
            "",
            "  t = pulseIn(Echo, HIGH);",
            "  d = t / 59 + 1;",
            "",
            "  Serial.print(\"Distancia: \");",
            "  Serial.print(d);",
            "  Serial.println(\" cm\");",
            "",
            "  char bufDist[8];",
            "  snprintf(bufDist, sizeof(bufDist), \"%ld\", d);",
            "  client.publish(topicDistance, bufDist);",
            "",
            "  if (d < 40) {",
            "    digitalWrite(ledPin, HIGH);",
            "    client.publish(topicAlert, \"NEAR\");",
            "  } else {",
            "    digitalWrite(ledPin, LOW);",
            "    client.publish(topicAlert, \"CLEAR\");",
            "  }"
        ])

    def emit_loop_end(self):
        self.cpp_lines.append(f"  delay({self.interval});\n}}");

    def generate_diagram_json(self):
        diagram = {
            "version": 1,
            "author": "Carlos Ramírez",
            "editor": "wokwi",
            "parts": [
                { "type": "board-esp32-devkit-c-v4", "id": "esp", "top": -1.66, "left": -5.9, "rotate": 90, "attrs": {} },
                { "type": "wokwi-hc-sr04", "id": "ultrasonic1", "top": -65.7, "left": 168.7, "attrs": { "distance": "200" } },
                { "type": "wokwi-led", "id": "led2", "top": -34.8, "left": -35.2, "attrs": { "color": "red" } }
            ],
            "connections": [
                ["esp:TX", "$serialMonitor:RX", "", []],
                ["esp:RX", "$serialMonitor:TX", "", []],
                ["esp:GND.2", "ultrasonic1:GND", "black", ["v27.14", "h142.86"]],
                ["led2:A", "esp:13", "green", ["v0"]],
                ["led2:C", "esp:GND.1", "green", ["v0"]],
                ["ultrasonic1:VCC", "esp:3V3", "red", ["v0", "h-115.2"]],
                ["ultrasonic1:TRIG", "esp:2", "orange", ["v163.2", "h-259.6"]],
                ["ultrasonic1:ECHO", "esp:4", "green", ["v182.4", "h-10.4"]]
            ],
            "dependencies": {}
        }
        with open("Template/diagram.json", "w") as f:
            json.dump(diagram, f, indent=2)
        print("[GENERATOR] Archivo diagram.json generado para ULTRASONIC.")
