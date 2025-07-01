import json
from codegen.base_codegen import BaseCodeGenerator

class GasSensorCodeGenerator(BaseCodeGenerator):
    def __init__(self, tokens):
        super().__init__(tokens)
        self.topics = {}
        self.sensor = None
        self.interval = 1000
        self.broker = ""
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
                self.expect(273)
                self.index += 1  # port
                self.expect(270)

            elif token_type == 314:  # SET
                self.index += 1
                _, self.sensor = self.current()
                self.sensor = self.sensor.upper()
                self.index += 1
                if self.sensor == "GASSENSOR":
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
                self.index += 2  # ID, (
                _, val = self.current()
                self.interval = int(val)
                self.index += 1
                self.expect(270)
                self.expect(275)
                self.emit_loop_start()
                while self.current()[0] in [302, 315]:
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
            '#define gasPin   36',
            '#define ledPin   2',
            '',
            '// Wi-Fi',
            'const char* ssid     = "Wokwi-GUEST";',
            'const char* password = "";',
            '',
            f'const char* mqtt_server = "{self.broker}";',
        ])
        for name, topic in self.topics.items():
            if "VALUE" in name:
                self.header_lines.append(f'const char* topicGasValue = "{topic}";')
            elif "ALERT" in name:
                self.header_lines.append(f'const char* topicGasAlert = "{topic}";')

        self.header_lines.extend([
            '',
            'WiFiClient espClient;',
            'PubSubClient client(espClient);',
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
            'void callback(char* topic, byte* payload, unsigned int length) {}',
            '',
            'void reconnect() {',
            '  while (!client.connected()) {',
            '    Serial.print("Intentando MQTT...");',
            '    String clientId = "ESP32GasSensor-";',
            '    clientId += String(random(0xffff), HEX);',
            '    if (client.connect(clientId.c_str())) {',
            '      Serial.println("Conectado");',
            '    } else {',
            '      Serial.print("Falló, rc=");',
            '      Serial.print(client.state());',
            '      Serial.println(" reintentando en 5s");',
            '      delay(5000);',
            '    }',
            '  }',
            '}',
            '',
            'void setup() {',
            '  Serial.begin(115200);',
            '  pinMode(gasPin, INPUT);',
            '  pinMode(ledPin, OUTPUT);',
            '  digitalWrite(ledPin, LOW);',
            '',
            '  setup_wifi();',
            '  client.setServer(mqtt_server, 1883);',
            '  client.setCallback(callback);',
            '}',
            ''
        ])

    def emit_loop_start(self):
        self.loop_lines.extend([
            'void loop() {',
            '  if (!client.connected()) { reconnect(); }',
            '  client.loop();',
            '',
            '  int gasValue = analogRead(gasPin);',
            '  Serial.print("Gas Sensor Value: ");',
            '  Serial.print(gasValue);',
            '',
            '  char bufValue[6];',
            '  snprintf(bufValue, sizeof(bufValue), "%d", gasValue);',
            '  client.publish(topicGasValue, bufValue);',
            ''
        ])

    def emit_loop_end(self):
        self.loop_lines.extend([
            '  if (gasValue <= 700) {',
            '    digitalWrite(ledPin, HIGH);',
            '    Serial.println(" --> Danger! Gas leak detected!");',
            '    client.publish(topicGasAlert, "DANGER");',
            '  } else {',
            '    digitalWrite(ledPin, LOW);',
            '    Serial.println(" --> Environment safe");',
            '    client.publish(topicGasAlert, "SAFE");',
            '  }',
            '',
            f'  delay({self.interval});',
            '}'
        ])

    def timer_action(self):
        if self.match(302):  # PUBLISH
            self.expect(269)
            _, topic = self.tokens[self.index]
            self.index += 1
            self.expect(273)
            self.index += 1
            if self.match(277):
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
            "author": "Divya Kardile",
            "editor": "wokwi",
            "parts": [
                { "type": "board-esp32-devkit-c-v4", "id": "esp", "top": 38.4, "left": 72.04, "attrs": {} },
                { "type": "wokwi-led", "id": "led1", "top": 25.2, "left": 215, "attrs": { "color": "red" } },
                { "type": "wokwi-gas-sensor", "id": "gas1", "top": 98.7, "left": -98.6, "attrs": {} }
            ],
            "connections": [
                [ "esp:TX", "$serialMonitor:RX", "", [] ],
                [ "esp:RX", "$serialMonitor:TX", "", [] ],
                [ "gas1:VCC", "esp:5V", "red", [ "h9.6", "v95.1" ] ],
                [ "gas1:GND", "esp:GND.1", "black", [ "h19.2", "v56.8" ] ],
                [ "gas1:DOUT", "esp:VP", "green", [ "h19.2", "v-115.5", "h134.4", "v172.8" ] ],
                [ "led1:C", "esp:GND.3", "green", [ "v0" ] ],
                [ "led1:A", "esp:2", "green", [ "v0" ] ]
            ],
            "dependencies": {}
        }
        with open("Template/diagram.json", "w") as f:
            json.dump(diagram, f, indent=2)
        print("[GENERATOR] Archivo Template/diagram.json generado correctamente.")
