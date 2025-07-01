import json
from codegen.base_codegen import BaseCodeGenerator

class PhotoresistorCodeGenerator(BaseCodeGenerator):
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
                _, port = self.tokens[self.index]
                self.index += 1
                self.expect(270)

            elif token_type == 314:  # SET
                self.index += 1
                _, self.sensor = self.current()
                self.sensor = self.sensor.upper()
                self.index += 1
                if self.sensor == "PHOTORESISTOR":
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
                self.expect(275)  # {
                self.emit_loop_start()
                while self.current()[0] in [302, 315]:  # PUBLISH or PRINT
                    self.timer_action()
                self.expect(276)  # }
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
            '#define analogPin   35',
            '#define digitalPin  13',
            '#define ledPin      2',
            '',
            '// Constantes para cálculo de lux',
            '#define GAMMA 0.7',
            '#define RL10  50',
            '',
            '// Wi-Fi',
            'const char* ssid     = "Wokwi-GUEST";',
            'const char* password = "";',
            '',
            f'const char* mqtt_server = "{self.broker}";',
        ])
        for name, topic in self.topics.items():
            if "LUX" in name:
                self.header_lines.append(f'const char* phot_lux = "{topic}";')
            elif "STATUS" in name:
                self.header_lines.append(f'const char* phot_status = "{topic}";')

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
            '    String clientId = "ESP32PhotoSensor-";',
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
            '  pinMode(analogPin, INPUT);',
            '  pinMode(digitalPin, INPUT);',
            '  pinMode(ledPin, OUTPUT);',
            '  digitalWrite(ledPin, LOW);',
            '',
            '  analogSetPinAttenuation(analogPin, ADC_11db);',
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
            '  int analogValue = analogRead(analogPin);',
            '  float voltage = analogValue / 4096.0 * 3.3;',
            '  float resistance = RL10 * 1e3 * voltage / (3.3 - voltage);',
            '  float lux = pow(RL10 * 1e3 * pow(10, GAMMA) / resistance, 1.0 / GAMMA);',
            '',
            '  int digitalValue = digitalRead(digitalPin);',
            '  bool isDark = (digitalValue == 1);',
            '',
            '  char bufLux[16];',
            '  snprintf(bufLux, sizeof(bufLux), "%.2f", lux);',
            '  client.publish(phot_lux, bufLux);',
            ''
        ])

    def emit_loop_end(self):
        self.loop_lines.extend([
            '  if (isDark) {',
            '    digitalWrite(ledPin, HIGH);',
            '    Serial.print("Lux: "); Serial.print(bufLux);',
            '    Serial.println(" --> DARK: Luz insuficiente");',
            '    client.publish(phot_status, "DARK");',
            '  } else {',
            '    digitalWrite(ledPin, LOW);',
            '    Serial.print("Lux: "); Serial.print(bufLux);',
            '    Serial.println(" --> LIGHT: Ambiente iluminado");',
            '    client.publish(phot_status, "LIGHT");',
            '  }',
            '',
            f'  delay({self.interval});',
            '}'
        ])

    def timer_action(self):
        # Avanza y consume las acciones dentro del timer (PUBLISH o PRINT)
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
            "author": "autor",
            "editor": "wokwi",
            "parts": [
                { "type": "board-esp32-devkit-c-v4", "id": "esp", "top": -57.6, "left": 52.84, "attrs": {} },
                { "type": "wokwi-led", "id": "led1", "top": -65.2, "left": 185, "attrs": { "color": "red" } },
                { "type": "wokwi-photoresistor-sensor", "id": "ldr1", "top": 22.4, "left": -191.2, "attrs": {} }
            ],
            "connections": [
                [ "esp:TX", "$serialMonitor:RX", "", [] ],
                [ "esp:RX", "$serialMonitor:TX", "", [] ],
                [ "ldr1:VCC", "esp:3V3", "red", [ "h0" ] ],
                [ "ldr1:GND", "esp:GND.1", "black", [ "h0" ] ],
                [ "ldr1:DO", "esp:13", "green", [ "h0" ] ],
                [ "ldr1:AO", "esp:12", "green", [ "h0" ] ],
                [ "led1:C", "esp:GND.3", "green", [ "v0" ] ],
                [ "led1:A", "esp:2", "green", [ "v0" ] ]
            ],
            "dependencies": {}
        }
        with open("Template/diagram.json", "w") as f:
            json.dump(diagram, f, indent=2)
        print("[GENERATOR] Archivo Template/diagram.json generado correctamente.")