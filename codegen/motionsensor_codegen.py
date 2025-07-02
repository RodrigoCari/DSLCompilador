import json
from codegen.base_codegen import BaseCodeGenerator

class MotionSensorCodeGenerator(BaseCodeGenerator):
    def __init__(self, tokens):
        super().__init__(tokens)
        self.topics = {}
        self.broker = ""
        self.interval = 1000
        self.sensor = None
        self.header_lines = []
        self.loop_lines = []
        self.footer_lines = []

    def generate(self):
        while self.index < len(self.tokens):
            token_type, lexeme = self.current()

            if token_type == 308:  # CONNECT
                self.index += 1
                self.expect(269)
                _, broker = self.tokens[self.index]
                self.broker = broker.strip('"')
                self.index += 1
                self.expect(273)  # ,
                self.index += 1  # port
                self.expect(270)

            elif token_type == 314:  # SET SENSOR
                self.index += 1
                _, self.sensor = self.current()
                self.sensor = self.sensor.upper()
                self.index += 1
                if self.sensor == "MOTIONSENSOR":
                    self.generate_diagram_json()

            elif token_type == 300:  # TOPIC
                self.index += 1
                _, name = self.current()
                self.index += 1
                self.expect(269)
                _, path = self.current()
                self.index += 1
                self.expect(270)
                self.topics[name] = path.strip('"')

            elif token_type == 303:  # TIMER
                self.index += 1
                self.index += 2  # Skip ID and (
                _, val = self.current()
                self.interval = int(val)
                self.index += 1
                self.expect(270)
                self.expect(275)
                self.emit_loop_start()
                while self.current()[0] in [302, 315]:  # PUBLISH or PRINT
                    self.timer_action()
                self.expect(276)
                self.emit_loop_end()

            else:
                self.index += 1

        self.emit_headers()
        return "\n".join(self.header_lines + self.loop_lines + self.footer_lines)

    def emit_headers(self):
        self.header_lines.extend([
            '#include <Arduino.h>',
            '#include <WiFi.h>',
            '#include <PubSubClient.h>',
            '',
            '// Pines',
            'const int pirPin = 2;',
            'const int ledPin = 5;',
            '',
            '// Wi-Fi',
            'const char* ssid     = "Wokwi-GUEST";',
            'const char* password = "";',
            '',
            f'const char* mqtt_server = "{self.broker}";',
        ])

        for name, topic in self.topics.items():
            if "STATE" in name.upper():
                self.header_lines.append(f'const char* topicState = "{topic}";')
            elif "STATUS" in name.upper():
                self.header_lines.append(f'const char* topicStatus = "{topic}";')

        self.header_lines.extend([
            '',
            'WiFiClient espClient;',
            'PubSubClient client(espClient);',
            '',
            '// Guarda el último estado para publicar solo cuando cambie',
            'int lastPirState = LOW;',
            '',
            'void setup_wifi() {',
            '  Serial.print("Conectando a ");',
            '  Serial.println(ssid);',
            '  WiFi.mode(WIFI_STA);',
            '  WiFi.begin(ssid, password);',
            '  while (WiFi.status() != WL_CONNECTED) {',
            '    delay(500);',
            '    Serial.print(".");',
            '  }',
            '  Serial.println("\\nWi-Fi OK, IP:");',
            '  Serial.println(WiFi.localIP());',
            '}',
            '',
            'void reconnect() {',
            '  while (!client.connected()) {',
            '    Serial.print("Intentando MQTT...");',
            '    String clientId = "ESP32Client-";',
            '    clientId += String(random(0xffff), HEX);',
            '    if (client.connect(clientId.c_str())) {',
            '      Serial.println("conectado");',
            '    } else {',
            '      Serial.print("falló rc=");',
            '      Serial.print(client.state());',
            '      Serial.println(" reintentando en 5s");',
            '      delay(5000);',
            '    }',
            '  }',
            '}',
            '',
            'void callback(char* topic, byte* payload, unsigned int length) {',
            '  // No se usa',
            '}',
            '',
            'void setup() {',
            '  pinMode(pirPin, INPUT);',
            '  pinMode(ledPin, OUTPUT);',
            '  digitalWrite(ledPin, LOW);',
            '',
            '  Serial.begin(115200);',
            '  setup_wifi();',
            '  client.setServer(mqtt_server, 1883);',
            '  client.setCallback(callback);',
            '}',
            ''
        ])

    def emit_loop_start(self):
        self.loop_lines.extend([
            'void loop() {',
            '  if (!client.connected()) reconnect();',
            '  client.loop();',
            '',
            '  int pirState = digitalRead(pirPin);',
            '  if (pirState != lastPirState) {',
            '    lastPirState = pirState;',
            '',
            '    digitalWrite(ledPin, pirState == HIGH ? HIGH : LOW);',
            '',
            '    char bufState[2];',
            '    char bufStatus[12];',
            '    snprintf(bufState, sizeof(bufState), "%d", pirState);',
            '    snprintf(bufStatus, sizeof(bufStatus), pirState == HIGH ? "MOTION" : "NO_MOTION");',
            '',
            '    client.publish(topicState, bufState);',
            '    client.publish(topicStatus, bufStatus);',
            '',
            '    Serial.print("PIR raw: ");',
            '    Serial.print(bufState);',
            '    Serial.print(" | Estado: ");',
            '    Serial.println(bufStatus);',
            '  }',
            ''
        ])

    def emit_loop_end(self):
        self.loop_lines.append(f'  delay({self.interval});')
        self.loop_lines.append('}')

    def timer_action(self):
        if self.match(302):  # PUBLISH
            self.expect(269)
            self.index += 1
            self.expect(273)
            self.index += 1
            if self.match(277):  # optional +
                self.index += 1
            self.expect(270)

        elif self.match(315):  # PRINT
            self.expect(269)
            while self.current()[0] != 270:
                self.index += 1
            self.expect(270)

    def generate_diagram_json(self):
        diagram = {
            "version": 1,
            "author": "Ulises Emmanuel Piscil Chino",
            "editor": "wokwi",
            "parts": [
                { "type": "wokwi-esp32-devkit-v1", "id": "esp", "top": 0, "left": 0, "attrs": {} },
                { "type": "wokwi-pir-motion-sensor", "id": "pir2", "top": 23.2, "left": -112.98, "attrs": {} },
                { "type": "wokwi-led", "id": "led2", "top": 34.8, "left": 138.2, "attrs": { "color": "red" } }
            ],
            "connections": [
                [ "esp:TX0", "$serialMonitor:RX", "", [] ],
                [ "esp:RX0", "$serialMonitor:TX", "", [] ],
                [ "led2:A", "esp:D5", "green", [ "v0" ] ],
                [ "led2:C", "esp:GND.1", "green", [ "v0" ] ],
                [ "pir2:GND", "esp:GND.2", "black", [ "v0" ] ],
                [ "pir2:OUT", "esp:D2", "green", [ "v0" ] ],
                [ "pir2:VCC", "esp:VIN", "red", [ "v0" ] ]
            ],
            "dependencies": {}
        }

        with open("Template/diagram.json", "w") as f:
            json.dump(diagram, f, indent=2)
        print("[GENERATOR] Archivo Template/diagram.json generado correctamente.")
