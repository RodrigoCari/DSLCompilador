class BaseCodeGenerator:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def current(self):
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return (None, None)

    def match(self, expected_type):
        if self.current()[0] == expected_type:
            self.index += 1
            return True
        return False

    def expect(self, expected_type):
        if not self.match(expected_type):
            raise ValueError(f"Expected token {expected_type} at index {self.index}, got {self.current()}")

    def generate(self):
        raise NotImplementedError("Subclases deben implementar este método.")
