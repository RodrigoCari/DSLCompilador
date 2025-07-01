class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def current(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else (None, None)

    def match(self, expected_type):
        if self.current()[0] == expected_type:
            self.index += 1
            return True
        return False

    def expect(self, expected_type):
        if not self.match(expected_type):
            raise SyntaxError(f"Expected token {expected_type} at index {self.index}, got {self.current()}")

    def parse(self):
        while self.index < len(self.tokens):
            self.statement()

    def statement(self):
        token_type, _ = self.current()

        if token_type == 308:  # CONNECT
            self.index += 1
            self.expect(269)    # (
            self.expect(400)    # STRING
            self.expect(273)    # ,
            self.expect(257)    # NUM  <--- CORREGIDO aquí
            self.expect(270)    # )

        elif token_type == 314:  # SET
            self.index += 1
            self.expect(256)     # ID

        elif token_type == 300:  # TOPIC
            self.index += 1
            self.expect(256)     # ID
            self.expect(269)     # (
            self.expect(400)     # STRING
            self.expect(270)     # )

        elif token_type == 303:  # TIMER
            self.index += 1
            self.expect(256)     # ID
            self.expect(269)     # (
            self.expect(257)     # NUM
            self.expect(270)     # )
            self.expect(275)     # {
            while self.current()[0] in [302, 315]:  # PUBLISH or PRINT
                self.timer_action()
            self.expect(276)     # }

        else:
            raise SyntaxError(f"Unknown statement at index {self.index}: {token_type}")

    def timer_action(self):
        token_type, _ = self.current()

        if token_type == 302:  # PUBLISH
            self.index += 1
            self.expect(269)    # (
            self.expect(256)    # topic ID
            self.expect(273)    # ,
            self.expression()
            self.expect(270)    # )

        elif token_type == 315:  # PRINT
            self.index += 1
            self.expect(269)    # (
            self.expression()
            self.expect(270)    # )

    def expression(self):
        token_type, _ = self.current()

        if token_type == 400:  # STRING
            self.index += 1
            while self.match(258):  # +
                self.expression()

        elif token_type == 256:  # ID
            self.index += 1
            if self.match(277):    # .
                self.expect(256)   # attribute like LUX or STATUS

        else:
            raise SyntaxError(f"Invalid expression at index {self.index}: {token_type}")