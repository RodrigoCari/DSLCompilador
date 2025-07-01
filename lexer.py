import sys
import re

# Diccionario de palabras clave y tokens
RESERVED = {
    'TOPIC': 300,
    'ON_MESSAGE': 301,
    'PUBLISH': 302,
    'TIMER': 303,
    'RULE': 304,
    'FUNCTION': 305,
    'RETURN': 306,
    'IF': 307,
    'CONNECT': 308,
    'SUBSCRIBE': 309,
    'UNSUBSCRIBE': 310,
    'ACTIVATE': 311,
    'DEACTIVATE': 312,
    'CALL': 313,
    'SET': 314,
    'PRINT': 315,
}

# Tokens especiales
TOKENS = {
    '+': 258,
    '-': 259,
    '*': 260,
    '/': 261,
    '>': 262,
    '<': 263,
    '>=': 264,
    '<=': 265,
    '=': 266,
    '==': 267,
    '!=': 268,
    '(': 269,
    ')': 270,
    '[': 271,
    ']': 272,
    ',': 273,
    ';': 274,
    '{': 275,
    '}': 276,
    '.': 277,
}

FLOAT = 255
ID = 256
NUM = 257

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.length = len(source)
        self.lexeme = ''

    def next_char(self):
        if self.pos < self.length:
            c = self.source[self.pos]
            self.pos += 1
            return c
        return None

    def peek(self):
        if self.pos < self.length:
            return self.source[self.pos]
        return None

    def skip_whitespace_and_comments(self):
        while True:
            c = self.peek()
            if c is None:
                return
            if c.isspace():
                self.next_char()
            elif c == '/':
                self.next_char()
                if self.peek() == '/':
                    while self.next_char() not in ['\n', None]:
                        pass
                elif self.peek() == '*':
                    self.next_char()
                    while True:
                        if self.next_char() == '*' and self.peek() == '/':
                            self.next_char()
                            break
                else:
                    self.pos -= 1
                    break
            else:
                break

    def get_token(self):
        self.skip_whitespace_and_comments()
        c = self.next_char()
        if c is None:
            return None, None

        # Identificador o palabra clave
        if c.isalpha() or c == '_':
            lex = c
            while (self.peek() and (self.peek().isalnum() or self.peek() == '_')):
                lex += self.next_char()
            self.lexeme = lex
            return RESERVED.get(lex.upper(), ID), lex

        # Número (entero o float)
        if c.isdigit():
            lex = c
            is_float = False
            while self.peek() and self.peek().isdigit():
                lex += self.next_char()
            if self.peek() == '.' and self.pos + 1 < self.length and self.source[self.pos + 1].isdigit():
                lex += self.next_char()  # añadir '.'
                is_float = True
                while self.peek() and self.peek().isdigit():
                    lex += self.next_char()
            self.lexeme = lex
            return FLOAT if is_float else NUM, lex

        # Operadores de dos caracteres
        two_char = c + (self.peek() or '')
        if two_char in TOKENS:
            self.next_char()
            self.lexeme = two_char
            return TOKENS[two_char], two_char

        # Operadores de un carácter
        if c in TOKENS:
            self.lexeme = c
            return TOKENS[c], c
        
        # Cadena entre comillas dobles
        if c == '"':
            lex = ''
            while True:
                nxt = self.peek()
                if nxt is None:
                    break
                if nxt == '"':
                    self.next_char()  # consume closing quote
                    break
                lex += self.next_char()
            self.lexeme = lex
            return 400, lex
        
        # No reconocido
        return None, c

    def scan_all(self):
        while True:
            token, lexeme = self.get_token()
            if token is None:
                break
            self.show_token(token, lexeme)
    
    def show_token(self, token, lexeme):
        # Invertimos el diccionario para imprimir nombres
        reserved_names = {v:k for k,v in RESERVED.items()}
        token_names = {
            255: "FLOAT",
            256: "ID",
            257: "NUM",
            258: "SUMA [+]",
            259: "RESTA [-]",
            260: "MULTIPLICACION [*]",
            261: "DIVISION [/]",
            262: "MAYOR [>]",
            263: "MENOR [<]",
            264: "MAYORIGUAL [>=]",
            265: "MENORIGUAL [<=]",
            266: "IGUAL [=]",
            267: "IGUALIGUAL [==]",
            268: "DISTINTO [!=]",
            269: "PARI [(]",
            270: "PARF [)]",
            271: "CORCHETEABIERTO [[ ]",
            272: "CORCHETECERRADO [] ]",
            273: "COMA [,]",
            274: "PUNTOYCOMA [;]",
            275: "LLAVEABIERTO [{]",
            276: "LLAVECERRADO [}]",
            277: "PUNTO [.]",
            400: "STRING"
        }

        if token == ID:
            print(f"token = ID [{lexeme}]")
        elif token == NUM:
            print(f"token = NUM [{lexeme}]")
        elif token == FLOAT:
            print(f"token = FLOAT [{lexeme}]")
        elif token in RESERVED.values():
            print(f"token = {reserved_names[token]} [{lexeme}]")
        elif token == 400:
            print(f'token = STRING ["{lexeme}"]')
        elif token in token_names:
            print(f"token = {token_names[token]}")
        else:
            print(f"token = DESCONOCIDO [{lexeme}]")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} archivo.txt")
        sys.exit(1)
    with open(sys.argv[1], "r") as f:
        source_code = f.read()

    lexer = Lexer(source_code)
    lexer.scan_all()
