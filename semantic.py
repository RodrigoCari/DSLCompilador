class SemanticAnalyzer:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.topics = set()
        self.sensors = set()
        self.broker = None

        # Diccionario de atributos válidos por tipo de sensor
        self.SENSOR_ATTRIBUTES = {
            "PHOTORESISTOR": {"LUX", "STATUS"},
            "GASSENSOR": {"VALUE", "ALERT"},
            "ULTRASONIC": {"DISTANCE", "ALERT"},
            "TEMPSENSOR": {"VALUE", "ALERT"},
            "MOTIONSENSOR": {"STATE", "STATUS"},
            "POTENTIOMETER": {"RAW", "VOLTAGE"},
        }

    def analyze(self):
        while self.index < len(self.tokens):
            self.statement()

    def current(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else (None, None)

    def match(self, expected_type):
        if self.current()[0] == expected_type:
            self.index += 1
            return True
        return False

    def expect(self, expected_type):
        if not self.match(expected_type):
            raise ValueError(f"Expected token {expected_type} at index {self.index}, got {self.current()}")

    def statement(self):
        token_type, _ = self.current()

        if token_type == 308:  # CONNECT("broker", 1883)
            self.index += 1
            self.expect(269)
            _, broker = self.current()
            self.index += 1
            self.expect(273)
            self.index += 1
            self.expect(270)
            self.broker = broker

        elif token_type == 300:  # TOPIC ID ( "..." )
            self.index += 1
            _, topic_id = self.current()
            self.topics.add(topic_id)
            self.index += 4

        elif token_type == 314:  # SET SENSOR
            self.index += 1
            _, sensor_id = self.current()
            self.sensors.add(sensor_id.upper())
            self.index += 1

        elif token_type == 303:  # TIMER ID (NUM) { ... }
            self.index += 1
            self.index += 2
            self.index += 2
            self.expect(275)
            while self.current()[0] in [302, 315]:
                self.timer_action()
            self.expect(276)

        else:
            raise ValueError(f"Unknown statement at index {self.index}: {self.current()[0]}")

    def timer_action(self):
        token_type, _ = self.current()

        if token_type == 302:  # PUBLISH
            self.index += 1
            self.expect(269)
            _, topic = self.tokens[self.index]
            if topic not in self.topics:
                raise ValueError(f"Undeclared topic: {topic}")
            self.index += 2
            self.check_expression()
            self.expect(270)

        elif token_type == 315:  # PRINT
            self.index += 1
            self.expect(269)
            self.check_expression()
            self.expect(270)

    def check_expression(self):
        token_type, value = self.current()

        if token_type == 256:  # ID
            sensor = value.upper()
            self.index += 1
            if self.match(277):  # .
                attr_token, attr = self.current()
                attr = attr.upper()
                if sensor not in self.sensors:
                    raise ValueError(f"Sensor '{sensor}' not defined")
                if sensor not in self.SENSOR_ATTRIBUTES or attr not in self.SENSOR_ATTRIBUTES[sensor]:
                    raise ValueError(f"Invalid attribute '{attr}' for sensor '{sensor}'")
                self.index += 1
        elif token_type == 400:  # STRING
            self.index += 1
            while self.match(258):  # +
                self.check_expression()
        else:
            raise ValueError(f"Invalid expression at index {self.index}: {token_type}")
