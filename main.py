from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer

# Importar generadores
from codegen.photoresistor_codegen import PhotoresistorCodeGenerator
from codegen.gassensor_codegen import GasSensorCodeGenerator
# from codegen.otrosensor_codegen import OtroSensorCodeGenerator
from codegen.ultrasonic_codegen import UltrasonicCodeGenerator
from codegen.temperaturesensor_codegen import TemperatureSensorCodeGenerator

import sys

def select_codegen(sensor_name, tokens):
    sensor_name = sensor_name.upper()
    if sensor_name == "PHOTORESISTOR":
        return PhotoresistorCodeGenerator(tokens)
    elif sensor_name == "GASSENSOR":
        return GasSensorCodeGenerator(tokens)
    elif sensor_name == "ULTRASONIC":
        return UltrasonicCodeGenerator(tokens)
    elif sensor_name == "TEMPSENSOR":
        return TemperatureSensorCodeGenerator(tokens)
    else:
        raise ValueError(f"Error: Sensor '{sensor_name}' no tiene generador definido.")

def main():
    try:
        # Solicitar el nombre del archivo al usuario
        input_file = input("Ingrese el nombre del archivo .txt (por ejemplo, 'gassensor.txt'): ").strip()

        # Paso 1: leer el código fuente DSL
        with open(input_file, "r") as f:
            source_code = f.read()

        # Paso 2: análisis léxico
        lexer = Lexer(source_code)
        tokens = []
        while True:
            token, lexeme = lexer.get_token()
            if token is None:
                break
            tokens.append((token, lexeme))

        # Paso 3: análisis sintáctico
        try:
            parser = Parser(tokens)
            parser.parse()
            print("Syntax is valid.")
        except SyntaxError as e:
            print("Syntax error:", e)
            sys.exit(1)

        # Paso 4: análisis semántico
        try:
            semantic = SemanticAnalyzer(tokens)
            semantic.analyze()
            print("Analisis semantico correcto.")
        except Exception as e:
            print("Error semantico:", e)
            sys.exit(1)

        # Paso 5: identificar sensor y generar código
        sensor_name = None
        for idx, (ttype, lexeme) in enumerate(tokens):
            if ttype == 314 and idx + 1 < len(tokens):  # SET
                sensor_name = tokens[idx + 1][1]
                break

        if not sensor_name:
            raise Exception("No se encontró un sensor definido con 'SET' en el código fuente.")

        try:
            generator = select_codegen(sensor_name, tokens)
            cpp_code = generator.generate()
        except Exception as e:
            print("Error en la generación de código:", e)
            sys.exit(1)

        # Guardar el archivo generado
        with open("Template/src/main.cpp", "w") as f:
            f.write(cpp_code)

        print("Codigo C++ generado en Template/src/main.cpp")

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{input_file}'")
        sys.exit(1)
    except Exception as e:
        print("Error general:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
