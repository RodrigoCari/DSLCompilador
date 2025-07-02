import json
from codegen.base_codegen import BaseCodeGenerator

class TemperatureSensorCodeGenerator(BaseCodeGenerator):
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
                self.index += 1  # port (ignored)
                self.expect(270)

            elif token_type == 314:  # SET
                self.index += 1
                _, self.sensor = self.current()
                self.sensor = self.sensor.upper()
                self.index += 1
                if self.sensor == "TEMPSENSOR":
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
                self.index += 2  # PUBLISH_LIGHT, (
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
            '#include <math.h>',
            '',
            '// Pines',
            'const int tempPin = 32;',
            'const int ledPin = 14;',
            'const float BETA = 3950;',
            '',
            '// Wi-Fi',
            'const char* ssid     = "Wokwi-GUEST";',
            'const char* password = "";',
            '',
            f'const char* mqtt_server = "{self.broker}";',
        ])

        # MQTT Topics
        for name, topic in self.topics.items():
            if "VALUE" in name:
                self.header_lines.append(f'const char* topicTemp = "{topic}";')
            elif "ALERT" in name:
                self.header_lines.append(f'const char* topicAlert = "{topic}";')

        self.header_lines.extend([
            '',
            'WiFiClient espClient;',
            'PubSubClient client(espClient);',
            '',
            '// Última temperatura publicada',
            'float lastTemperature = -1000.0;',
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
            '    String clientId = "ESP32TempClient-";',
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
            'void setup() {',
            '  Serial.begin(9600);',
            '  analogReadResolution(10);',
            '  pinMode(tempPin, INPUT);',
            '  pinMode(ledPin, OUTPUT);',
            '  digitalWrite(ledPin, LOW);',
            '',
            '  setup_wifi();',
            '  client.setServer(mqtt_server, 1883);',
            '}',
            ''
        ])

    def emit_loop_start(self):
        self.loop_lines.extend([
            'void loop() {',
            '  if (!client.connected()) { reconnect(); }',
            '  client.loop();',
            '',
            '  int analogValue = analogRead(tempPin);',
            '  float celsius = 1 / (log(1 / (1023. / analogValue - 1)) / BETA + 1.0 / 298.15) - 273.15;',
            '',
            '  Serial.print("Temperature: ");',
            '  Serial.print(celsius);',
            '  Serial.println(" °C");',
            '',
            '  char bufTemp[8];',
            '  dtostrf(celsius, 1, 2, bufTemp);',
            '  client.publish(topicTemp, bufTemp);',
            ''
        ])

    def emit_loop_end(self):
        self.loop_lines.extend([
            '  if (celsius >= 35.0) {',
            '    digitalWrite(ledPin, HIGH);',
            '    client.publish(topicAlert, "ALERTA");',
            '  } else {',
            '    digitalWrite(ledPin, LOW);',
            '    client.publish(topicAlert, "OK");',
            '  }',
            '',
            f'  delay({self.interval});',
            '}'
        ])

    def timer_action(self):
        # PUBLISH(TEMP_VALUE, TEMPSENSOR.VALUE)
        if self.match(302):  # PUBLISH
            self.expect(269)
            self.index += 1  # topic
            self.expect(273)
            self.index += 1  # sensor.value
            if self.match(277):  # optional '+'
                self.index += 1
            self.expect(270)

        # PRINT("Value: " + TEMPSENSOR.VALUE + ...)
        elif self.match(315):  # PRINT
            self.expect(269)
            while self.current()[0] != 270:
                self.index += 1
            self.expect(270)

    def generate_diagram_json(self):
        diagram = {
            "version": 1,
            "author": "Shaggy",
            "editor": "wokwi",
            "parts": [
                { "type": "wokwi-esp32-devkit-v1", "id": "esp", "top": -36.39, "left": -2.8, "attrs": {} },
                {
                    "type": "wokwi-ntc-temperature-sensor",
                    "id": "ntc1",
                    "top": -33.68,
                    "left": 131.38,
                    "rotate": 90,
                    "attrs": {}
                },
                {
                    "type": "wokwi-led",
                    "id": "led1",
                    "top": -31.59,
                    "left": -84.06,
                    "attrs": { "color": "red" }
                },
                {
                    "type": "wokwi-resistor",
                    "id": "r1",
                    "top": 101.21,
                    "left": -121.88,
                    "attrs": { "value": "5600" }
                }
            ],
            "connections": [
                [ "esp:TX0", "$serialMonitor:RX", "", [] ],
                [ "esp:RX0", "$serialMonitor:TX", "", [] ],
                [ "esp:GND.1", "ntc1:GND", "black", [ "h0" ] ],
                [ "ntc1:VCC", "esp:3V3", "red", [ "v0" ] ],
                [ "ntc1:OUT", "esp:D32", "green", [ "v0" ] ],
                [ "r1:1", "led1:C", "green", [ "h-7.64", "v2.81" ] ],
                [ "led1:A", "esp:D14", "green", [ "v0" ] ],
                [ "r1:2", "esp:GND.2", "green", [ "h0" ] ]
            ]
        }

        with open("Template/diagram.json", "w") as f:
            json.dump(diagram, f, indent=2)
        print("[GENERATOR] Archivo Template/diagram.json generado correctamente.")
